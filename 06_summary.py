import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pygam import LinearGAM, f, s, te
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
Z95 = 1.959963984540054
SUBSAMPLE_CELLS = 10000
SEED = 42
FIG2_BINS = 20
LAM_GRID = [0.1, 1.0, 10.0, 100.0, 1000.0]


def intervals_overlap(a_low, a_high, b_low, b_high):
    return not (a_high < b_low or b_high < a_low)


def fmt_lam(value):
    return f"{value:g}"


def fig2_curves(panel, selected_lam):
    """Recompute the Fig 2 total-effect lines and 95% bands from the panel.

    This repeats the fixed part of step 05 without changing the model,
    subsample, bins or smoothing. It is used only for summary claims.
    """
    cell_ids = panel["grid_id"].unique()
    rng = np.random.default_rng(SEED)
    if len(cell_ids) > SUBSAMPLE_CELLS:
        sampled_cells = rng.choice(
            cell_ids, size=SUBSAMPLE_CELLS, replace=False
        )
        sub = panel[panel["grid_id"].isin(sampled_cells)].copy()
    else:
        sub = panel.copy()

    year_levels = sorted(int(year) for year in sub["year"].unique())
    sub["year_code"] = sub["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )
    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    terms = s(0) + s(1) + te(0, 1) + f(2)
    gam = LinearGAM(terms, lam=selected_lam)
    gam.fit(X, y)

    q01, q99 = panel["built"].quantile([0.01, 0.99])
    eval_edges = np.linspace(q01, q99, FIG2_BINS + 1)
    eval_centers = 0.5 * (eval_edges[:-1] + eval_edges[1:])
    ndvi_quantiles = np.full((FIG2_BINS, 3), np.nan)
    valid_bins = np.zeros(FIG2_BINS, dtype=bool)
    for i in range(FIG2_BINS):
        if i < FIG2_BINS - 1:
            in_bin = (panel["built"] >= eval_edges[i]) & (
                panel["built"] < eval_edges[i + 1]
            )
        else:
            in_bin = (panel["built"] >= eval_edges[i]) & (
                panel["built"] <= eval_edges[i + 1]
            )
        values = panel.loc[in_bin, "ndvi"]
        if len(values) >= 5:
            ndvi_quantiles[i] = np.quantile(values, [0.25, 0.5, 0.75])
            valid_bins[i] = True

    unique_built = panel.drop_duplicates("grid_id")["built"]
    bin_cell_counts = np.zeros(FIG2_BINS, dtype=int)
    for i in range(FIG2_BINS):
        if i < FIG2_BINS - 1:
            in_bin_cells = (unique_built >= eval_edges[i]) & (
                unique_built < eval_edges[i + 1]
            )
        else:
            in_bin_cells = (unique_built >= eval_edges[i]) & (
                unique_built <= eval_edges[i + 1]
            )
        bin_cell_counts[i] = int(in_bin_cells.sum())

    eval_rows = []
    for i in range(FIG2_BINS):
        if not valid_bins[i]:
            continue
        for q in range(3):
            eval_rows.append([eval_centers[i], ndvi_quantiles[i, q], 0.0])
    X_eval = np.array(eval_rows)
    n_valid = int(valid_bins.sum())

    s_effect = gam.partial_dependence(term=0, X=X_eval)
    te_effect = gam.partial_dependence(term=2, X=X_eval)
    point_total = s_effect + te_effect

    design = gam._modelmat(X_eval)
    offsets = np.cumsum([0] + [int(term.n_coefs) for term in gam.terms])
    cols_built = np.arange(offsets[0], offsets[1])
    cols_te = np.arange(offsets[2], offsets[3])
    cols = np.concatenate([cols_built, cols_te])
    Z = np.hstack(
        [
            design[:, cols_built].toarray(),
            design[:, cols_te].toarray(),
        ]
    )
    covariance = gam.statistics_["cov"][np.ix_(cols, cols)]
    total = Z @ gam.coef_[cols]
    if not np.allclose(total, point_total, atol=1e-8):
        raise SystemExit("total effect does not match term sum")
    variance = np.einsum("ij,jk,ik->i", Z, covariance, Z)
    standard_error = np.sqrt(np.maximum(variance, 0.0))
    lower = total - Z95 * standard_error
    upper = total + Z95 * standard_error

    return (
        total.reshape(n_valid, 3),
        lower.reshape(n_valid, 3),
        upper.reshape(n_valid, 3),
        eval_centers[valid_bins],
        float(q01),
        float(q99),
        n_valid,
        bin_cell_counts[valid_bins],
        int(len(unique_built)),
    )


def direction_label(start_min, start_max, end_min, end_max, total_min, total_max):
    start_mid = 0.5 * (start_min + start_max)
    end_mid = 0.5 * (end_min + end_max)
    delta = end_mid - start_mid
    span = total_max - total_min
    if abs(delta) < 0.2:
        return "roughly flat"
    if span > 1.5 * abs(delta) + 0.2:
        return "non-monotonic"
    return "rises" if delta > 0 else "falls"


def zero_crossing_text(p50, centers):
    for i in range(1, len(p50)):
        if (p50[i - 1] <= 0 <= p50[i]) or (p50[i - 1] >= 0 >= p50[i]):
            denominator = p50[i - 1] - p50[i]
            fraction = p50[i - 1] / denominator if denominator else 0.0
            crossing = centers[i - 1] + fraction * (
                centers[i] - centers[i - 1]
            )
            return f"crosses zero near built {crossing:.2f}"
    return "does not cross zero inside the plotted range"


def vegetation_result_v2(panel, selected_lam):
    """Evaluate vegetation moderation under convention v2.

    Computes:
    1. Paired 5 km spatial-block GroupKFold CV R2 for additive vs full model.
    2. Gap contrast between the lowest and highest built bins with >= VEG_MIN_BLOCKS.
    """
    block_key = (
        np.floor(panel["x"] / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(panel["y"] / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    panel = panel.copy()
    panel["block_id"] = block_key

    q01 = float(np.quantile(panel["built"], 0.01))
    q99 = float(np.quantile(panel["built"], 0.99))
    eval_edges = np.linspace(q01, q99, FIG2_BINS + 1)
    eval_centers = 0.5 * (eval_edges[:-1] + eval_edges[1:])
    unique_cells_total = panel["grid_id"].nunique()

    bin_stats = []
    ndvi_quantiles = np.zeros((FIG2_BINS, 3))
    valid_bins = np.zeros(FIG2_BINS, dtype=bool)

    for i in range(FIG2_BINS):
        in_bin = (panel["built"] >= eval_edges[i]) & (
            panel["built"] <= eval_edges[i + 1]
            if i == FIG2_BINS - 1
            else panel["built"] < eval_edges[i + 1]
        )
        sub_bin = panel[in_bin]
        u_cells = sub_bin["grid_id"].nunique()
        u_share = u_cells / unique_cells_total if unique_cells_total else 0.0
        n_blocks = sub_bin["block_id"].nunique()

        values = sub_bin["ndvi"]
        if len(values) >= 5:
            ndvi_quantiles[i] = np.quantile(values, [0.25, 0.5, 0.75])
            valid_bins[i] = True

        bin_stats.append(
            {
                "bin": i + 1,
                "center": eval_centers[i],
                "u_cells": u_cells,
                "u_share": u_share,
                "n_blocks": n_blocks,
                "valid": valid_bins[i],
            }
        )
    df_bins = pd.DataFrame(bin_stats)

    cell_ids = panel["grid_id"].unique()
    rng = np.random.default_rng(SEED)
    if len(cell_ids) > SUBSAMPLE_CELLS:
        sampled_cells = rng.choice(cell_ids, size=SUBSAMPLE_CELLS, replace=False)
        sub = panel[panel["grid_id"].isin(sampled_cells)].copy()
    else:
        sub = panel.copy()

    year_levels = sorted(int(year) for year in sub["year"].unique())
    sub["year_code"] = sub["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )

    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    groups = pd.factorize(sub["block_id"])[0]
    splits = list(GroupKFold(n_splits=config.CV_FOLDS).split(X, y, groups))

    def cv_scores(terms, lam):
        scores = []
        for train_index, test_index in splits:
            fold = LinearGAM(terms, lam=lam)
            fold.fit(X[train_index], y[train_index])
            prediction = fold.predict(X[test_index])
            scores.append(float(r2_score(y[test_index], prediction)))
        return scores

    full_terms = s(0) + s(1) + te(0, 1) + f(2)
    gam = LinearGAM(full_terms, lam=selected_lam)
    gam.fit(X, y)
    full_scores = cv_scores(full_terms, gam.lam)

    add_terms = s(0) + s(1) + f(2)
    add_gam = LinearGAM(add_terms)
    add_gam.gridsearch(X, y, lam=LAM_GRID, progress=False)
    add_scores = cv_scores(add_terms, add_gam.lam)

    diffs = [f_sc - a_sc for f_sc, a_sc in zip(full_scores, add_scores)]
    mean_diff = float(np.mean(diffs))
    folds_favour = int(sum(d > 0 for d in diffs))

    cand_bins = df_bins[
        (df_bins["n_blocks"] >= config.VEG_MIN_BLOCKS) & df_bins["valid"]
    ]
    if len(cand_bins) < 2:
        raise SystemExit("Fewer than 2 bins meet the minimum block threshold")
    bin_low = cand_bins.iloc[0]
    bin_high = cand_bins.iloc[-1]
    i_low = int(bin_low["bin"] - 1)
    i_high = int(bin_high["bin"] - 1)

    eval_pts = [
        [eval_centers[i_low], ndvi_quantiles[i_low, 0], 0.0],
        [eval_centers[i_low], ndvi_quantiles[i_low, 2], 0.0],
        [eval_centers[i_high], ndvi_quantiles[i_high, 0], 0.0],
        [eval_centers[i_high], ndvi_quantiles[i_high, 2], 0.0],
    ]
    X_pts = np.array(eval_pts)
    design = gam._modelmat(X_pts)
    offsets = np.cumsum([0] + [int(term.n_coefs) for term in gam.terms])
    cols_built = np.arange(offsets[0], offsets[1])
    cols_te = np.arange(offsets[2], offsets[3])
    cols = np.concatenate([cols_built, cols_te])
    Z = np.hstack(
        [design[:, cols_built].toarray(), design[:, cols_te].toarray()]
    )
    covariance = gam.statistics_["cov"][np.ix_(cols, cols)]

    Z_contrast = (Z[3] - Z[2]) - (Z[1] - Z[0])
    contrast_val = float(Z_contrast @ gam.coef_[cols])
    var_contrast = float(Z_contrast @ covariance @ Z_contrast)
    se_contrast = float(np.sqrt(max(var_contrast, 0.0)))
    z = contrast_val / se_contrast if se_contrast > 0 else 0.0

    cond_z = abs(z) > config.VEG_CONTRAST_Z_THRESHOLD
    cond_cv = (folds_favour >= config.VEG_CV_MIN_FOLDS) and (
        mean_diff > config.VEG_CV_MEAN_GAIN_THRESHOLD
    )

    if cond_z and cond_cv:
        outcome = "supported"
    elif cond_z or cond_cv:
        outcome = "weak or inconclusive"
    else:
        outcome = "not supported"

    low_b = int(bin_low["bin"])
    high_b = int(bin_high["bin"])
    low_sh = float(bin_low["u_share"])
    high_sh = float(bin_high["u_share"])
    low_bl = int(bin_low["n_blocks"])
    high_bl = int(bin_high["n_blocks"])

    text = (
        f"{outcome}: gap contrast between bin {low_b} ({low_sh:.1%} cells, {low_bl} blocks) "
        f"and bin {high_b} ({high_sh:.1%} cells, {high_bl} blocks) is {contrast_val:+.2f} K "
        f"(SE {se_contrast:.2f} K, z = {z:+.2f}; SE ignores spatial autocorrelation); "
        f"full model beats additive model in {folds_favour} of {config.CV_FOLDS} folds "
        f"with mean gain {mean_diff:+.3f} R2"
    )

    rule = (
        "Outcomes are conventions chosen after seeing the results: 'supported' means |z| > 2 for "
        "the gap contrast between lowest and highest bins with at least 30 distinct 5 km blocks AND "
        "the full model beats the additive model in at least 4 of 5 folds with mean gain > 0.01 R2; "
        "'weak or inconclusive' means exactly one of those holds; 'not supported' means neither holds. "
        "The contrast SE is from the coefficient covariance and ignores spatial autocorrelation."
    )

    return text, rule


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    output_dir = Path("outputs") / city
    gradient = pd.read_csv(output_dir / "gradient.csv")
    with open(output_dir / "cv.json") as handle:
        cv = json.load(handle)
    panel = pd.read_parquet(Path("data") / city / "panel.parquet")

    medians = gradient.pivot(
        index="class", columns="year", values="median"
    ).reindex(CLASS_ORDER)
    dense = gradient[gradient["class"] == "dense"].set_index("year")
    dense_counts = panel[panel["ladder_class"] == 23].groupby("year").size()
    years = list(config.YEARS)

    pairs = [
        (years[0], years[1]),
        (years[0], years[2]),
        (years[1], years[2]),
    ]
    overlap = {
        pair: intervals_overlap(
            dense.loc[pair[0], "ci_low"],
            dense.loc[pair[0], "ci_high"],
            dense.loc[pair[1], "ci_low"],
            dense.loc[pair[1], "ci_high"],
        )
        for pair in pairs
    }
    if all(overlap.values()):
        separation = (
            "The 95% bootstrap intervals overlap for all year pairs, "
            "so they do not separate the class 23 medians."
        )
    else:
        separated = [
            f"{left} vs {right}"
            for (left, right), does_overlap in overlap.items()
            if not does_overlap
        ]
        separation = (
            "The 95% bootstrap intervals separate "
            + ", ".join(separated)
            + "; the other pairs overlap."
        )

    class_rows = []
    for name in CLASS_ORDER:
        values = " | ".join(
            f"{medians.loc[name, year]:.2f}" for year in years
        )
        class_rows.append(f"| {name} | {values} |")
    class_table = "\n".join(class_rows)

    dense_lines = []
    for year in years:
        row = dense.loc[year]
        dense_lines.append(
            f"- {year}: {int(dense_counts.loc[year]):,} cells, "
            f"median {row['median']:+.2f} K, "
            f"95% interval [{row['ci_low']:+.2f}, {row['ci_high']:+.2f}]"
        )
    dense_text = "\n".join(dense_lines)
    dense_count_text = ", ".join(
        f"{int(dense_counts.loc[year]):,}" for year in years
    )

    comparisons = cv["model_comparisons"]["models"]
    ndvi = comparisons["ndvi_year"]
    built = comparisons["built_year"]
    full = comparisons["full"]
    comparison_rows = [
        f"| NDVI + year | {ndvi['r2_mean']:.3f} +/- {ndvi['r2_std']:.3f} | "
        f"{fmt_lam(ndvi['selected_lam'])} |",
        f"| Built + year | {built['r2_mean']:.3f} +/- {built['r2_std']:.3f} | "
        f"{fmt_lam(built['selected_lam'])} |",
        f"| Full model | {full['r2_mean']:.3f} +/- {full['r2_std']:.3f} | "
        f"{fmt_lam(full['selected_lam'])} |",
    ]
    comparison_table = "\n".join(comparison_rows)
    gain = cv["r2_mean"] - ndvi["r2_mean"]

    total_min = cv["built_total_min"]
    total_max = cv["built_total_max"]
    unsupported_words = cv["built_unsupported_words"]
    n04 = cv["n_cells_above_built_0.4"]
    n05 = cv["n_cells_above_built_0.5"]
    s04 = cv["share_above_built_0.4"]
    s05 = cv["share_above_built_0.5"]
    below01 = cv["share_below_built_0.1"]
    x0, x1 = cv["fig2_built_range"]

    (
        total_lines,
        lower_lines,
        upper_lines,
        centers,
        curve_x0,
        curve_x1,
        n_valid,
        bin_cell_counts,
        total_cells,
    ) = fig2_curves(panel, cv["selected_lam"])

    start_min = float(np.min(total_lines[0]))
    start_max = float(np.max(total_lines[0]))
    end_min = float(np.min(total_lines[-1]))
    end_max = float(np.max(total_lines[-1]))
    direction = direction_label(
        start_min,
        start_max,
        end_min,
        end_max,
        total_min,
        total_max,
    )
    crossing = zero_crossing_text(total_lines[:, 1], centers)
    veg_text, veg_rule = vegetation_result_v2(panel, cv["selected_lam"])

    direction_rule = (
        "Rule: direction is 'roughly flat' if |p50 end - p50 start| < 0.2 K, "
        "'non-monotonic' if the p50 range exceeds "
        "1.5 x |end - start| + 0.2 K, otherwise 'rises' or 'falls' from the "
        "sign of end - start; a zero crossing is reported when the p50 line "
        "changes sign inside the plotted range."
    )
    if direction in ("non-monotonic", "roughly flat"):
        direction_phrase = f"is {direction}"
    else:
        direction_phrase = direction
    curve_no_period = (
        f"{direction_phrase}; across the NDVI lines, "
        f"{start_min:+.1f} to {start_max:+.1f} K at built {x0:.2f} and "
        f"{end_min:+.1f} to {end_max:+.1f} K at built {x1:.2f}; "
        f"it {crossing}"
    )
    curve_core = f"{curve_no_period}."
    curve_text = f"the fitted total effect {curve_core}"
    cv_core = (
        f"NDVI + year {ndvi['r2_mean']:.3f}, built + year "
        f"{built['r2_mean']:.3f}, full {cv['r2_mean']:.3f}; the full model "
        f"gains {gain:.3f} R2 over NDVI + year"
    )
    cv_text = f"{cv_core}."

    lam_min = min(cv["lam_grid"])
    lam_max = max(cv["lam_grid"])
    if cv["selected_lam"] == lam_min:
        smoothing_edge = "at the lower edge"
    elif cv["selected_lam"] == lam_max:
        smoothing_edge = "at the upper edge"
    else:
        smoothing_edge = "inside the grid"

    summary = f"""# {city}: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is {medians.loc['centre', years[0]]:.2f}, {medians.loc['centre', years[1]]:.2f}, {medians.loc['centre', years[2]]:.2f} K in {years[0]}/{years[1]}/{years[2]}. Class 23 has {dense_count_text} cells in {years[0]}/{years[1]}/{years[2]}; its medians are {dense.loc[years[0], 'median']:+.2f}, {dense.loc[years[1], 'median']:+.2f}, {dense.loc[years[2], 'median']:+.2f} K. {separation}
- CV R2: {cv_text}
- Total built effect: `s(built) + te(built, NDVI)` {curve_core} {unsupported_words}
- Built fraction is zero-inflated: {below01:.1%} of cells are below 0.1 and {s04:.1%} are above 0.4 ({s05:.1%} above 0.5); the high-built part of the curve is sparse.
- H2 (nonlinearity): {curve_text} This is descriptive, not a formal test, and cells above built 0.4 are sparse ({n04:,}, {s04:.1%}).
- H2 (vegetation modification): {veg_text}.

## Median lst_rel by class (K)
| class | {years[0]} | {years[1]} | {years[2]} |
|---|---:|---:|---:|
{class_table}

## Class 23 detail
{dense_text}
{separation}

## Total built effect (Fig 2)
The fitted total effect {curve_core}

{direction_rule}

The fitted total effect ranges from {total_min:.2f} to {total_max:.2f} K over the 1st to 99th percentile of built ({x0:.2f} to {x1:.2f}). The plot uses {cv['fig2_built_bins']} built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a {cv['fig2_band']}.

Only {n04:,} cells ({s04:.2%}) are above built 0.4 and {n05:,} ({s05:.2%}) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `{cv['model']}`.
- Fit: {cv['subsample_cells']:,} randomly sampled cells, all available years, {cv['subsample_rows']:,} rows.
- Validation: {cv['n_folds']} folds, {cv['block_size_m']} m spatial blocks, GroupKFold.
- Full-model CV R2: mean {cv['r2_mean']:.3f}, spread {cv['r2_std']:.3f} (min {cv['r2_min']:.3f}, max {cv['r2_max']:.3f}).
- Convergence: {cv['converged']}.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R2 mean +/- spread | Selected lam |
|---|---:|---:|
{comparison_table}

{cv_text} Rule: the full-model gain is its CV R2 minus the NDVI + year CV R2; no qualitative 'dominant' label is used.

## Built fraction distribution
Built fraction is zero-inflated: {cv['n_cells_below_built_0.1']:,} cells ({below01:.1%}) are below 0.1, {n04:,} ({s04:.1%}) are above 0.4, and {n05:,} ({s05:.1%}) are above 0.5. The high-built part of the curve is sparse.

## Hypotheses
H2 (nonlinearity): {curve_text} This is descriptive, not a formal test, and high-built cells are sparse. H2 (vegetation modification): {veg_text}. {veg_rule}

## Caveats
- The outcome is satellite land surface temperature, not air temperature; heatwave claims are out of scope.
- GHSL classes are 1 km while the grid is 300 m, so class is context rather than a precise per-cell measurement.
- SMOD and BUILT-S are related products, so by-class and pooled results overlap in what they show.
- LST and NDVI come from the same Landsat scenes and share atmosphere and cloud effects; built fraction and NDVI are also negatively correlated, so the interaction term is interpreted cautiously.
- The GAM is fitted to a random subsample of {cv['subsample_cells']:,} cells; CV is on that subsample.
- The smoothing grid was {cv['lam_grid']}, and the selected smoothing was {cv['selected_lam']} {smoothing_edge}.
- The 95% band is conditional on the selected smoothing.
- Results are associations only, not causal effects.

## Three sentences
Done: I ran steps 01 to 06 for {city} for {years[0]}, {years[1]} and {years[2]}, fitting the GAM on a random subsample of {cv['subsample_cells']:,} cells ({cv['subsample_rows']:,} rows) with 5 km spatial-block cross-validation.
Shows: Centre-class median `lst_rel` is {medians.loc['centre', years[0]]:.2f}, {medians.loc['centre', years[1]]:.2f} and {medians.loc['centre', years[2]]:.2f} K in {years[0]}, {years[1]} and {years[2]}; {cv_core}; H2 nonlinearity: the fitted total effect {curve_no_period}; H2 vegetation modification: {veg_text}.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a {cv['subsample_cells']:,}-cell subsample and smoothing selected {smoothing_edge}, the 95% band is conditional on that smoothing, and all results are associations, not causal effects.
"""

    path = output_dir / "summary.md"
    path.write_text(summary, encoding="utf-8")
    print(f"{city}: wrote {path}")


if __name__ == "__main__":
    main()
