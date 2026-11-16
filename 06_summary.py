import argparse
import json
import time
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


def vegetation_result_v3(panel, selected_lam, n_boot, boot_seed):
    """Evaluate vegetation moderation under convention v3.

    Fixed NDVI contrast: the NDVI p25/p75 are computed city-wide over
    non-water cells (mean NDVI per unique cell), so the same NDVI values
    are used in every built bin, unlike v2 where within-bin quantiles made
    the NDVI range differ between bins. Contrast = (gap at bin 20) minus
    (gap at bin 1), where the gap is the total effect at NDVI p75 minus
    the total effect at NDVI p25. Model-based SE/z come from the
    coefficient covariance; a 5 km spatial-block bootstrap (blocks
    resampled with replacement, full GAM refit with the selected
    smoothing fixed, no new grid search) supplies the bootstrap CI.
    """
    t0 = time.time()
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

    # Fixed NDVI values: city-wide quantiles of per-cell mean NDVI.
    cells = panel.drop_duplicates("grid_id")[
        ["grid_id", "built", "x", "y", "block_id"]
    ].copy()
    cell_ndvi = panel.groupby("grid_id")["ndvi"].mean().rename("ndvi_mean")
    cells = cells.merge(cell_ndvi, on="grid_id")
    p25 = float(np.quantile(cells["ndvi_mean"], 0.25))
    p75 = float(np.quantile(cells["ndvi_mean"], 0.75))

    def bin_mask(i):
        if i < FIG2_BINS - 1:
            return (cells["built"] >= eval_edges[i]) & (
                cells["built"] < eval_edges[i + 1]
            )
        return (cells["built"] >= eval_edges[i]) & (
            cells["built"] <= eval_edges[i + 1]
        )

    i_low, i_high = 0, FIG2_BINS - 1
    for i, label in ((i_low, "bin 1"), (i_high, "bin 20")):
        if int(bin_mask(i).sum()) == 0:
            raise SystemExit(f"{label} has no cells")
    bin_cells_low = cells[bin_mask(i_low)]
    bin_cells_high = cells[bin_mask(i_high)]
    n_cells_total = len(cells)
    share_low_total = len(bin_cells_low) / n_cells_total
    share_high_total = len(bin_cells_high) / n_cells_total
    share_low_between = float(
        (
            (bin_cells_low["ndvi_mean"] >= p25)
            & (bin_cells_low["ndvi_mean"] <= p75)
        ).mean()
    )
    share_high_between = float(
        (
            (bin_cells_high["ndvi_mean"] >= p25)
            & (bin_cells_high["ndvi_mean"] <= p75)
        ).mean()
    )
    blocks_low = int(bin_cells_low["block_id"].nunique())
    blocks_high = int(bin_cells_high["block_id"].nunique())

    # Subsample identical to the step 05 fit; fixed-lam GAM fit.
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

    eval_pts = np.array(
        [
            [eval_centers[i_low], p25, 0.0],
            [eval_centers[i_low], p75, 0.0],
            [eval_centers[i_high], p25, 0.0],
            [eval_centers[i_high], p75, 0.0],
        ]
    )

    def contrast_from(fit):
        design = fit._modelmat(eval_pts)
        offsets = np.cumsum([0] + [int(term.n_coefs) for term in fit.terms])
        cols_built = np.arange(offsets[0], offsets[1])
        cols_te = np.arange(offsets[2], offsets[3])
        cols = np.concatenate([cols_built, cols_te])
        Z = np.hstack(
            [design[:, cols_built].toarray(), design[:, cols_te].toarray()]
        )
        covariance = fit.statistics_["cov"][np.ix_(cols, cols)]
        Z_contrast = (Z[3] - Z[2]) - (Z[1] - Z[0])
        val = float(Z_contrast @ fit.coef_[cols])
        var = float(Z_contrast @ covariance @ Z_contrast)
        se = float(np.sqrt(max(var, 0.0)))
        return val, se

    contrast_val, se_contrast = contrast_from(gam)
    z = contrast_val / se_contrast if se_contrast > 0 else 0.0

    # Spatial-block bootstrap of the contrast, smoothing fixed.
    boot_rng = np.random.default_rng(boot_seed)
    sub_blocks = sub["block_id"].unique()
    n_sub_blocks = len(sub_blocks)
    boot_contrasts = []
    for _ in range(n_boot):
        draw = boot_rng.choice(sub_blocks, size=n_sub_blocks, replace=True)
        rows = sub[sub["block_id"].isin(draw)]
        Xr = rows[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
        yr = rows["lst_rel"].to_numpy(dtype=float)
        try:
            fit = LinearGAM(full_terms, lam=selected_lam)
            fit.fit(Xr, yr)
            val_r, _ = contrast_from(fit)
            boot_contrasts.append(val_r)
        except Exception:
            continue
    boot_contrasts = np.array(boot_contrasts)
    n_boot_ok = int(len(boot_contrasts))
    if n_boot_ok == 0:
        raise SystemExit("bootstrap: no resample succeeded")
    boot_lo = float(np.percentile(boot_contrasts, 2.5))
    boot_hi = float(np.percentile(boot_contrasts, 97.5))
    if contrast_val != 0:
        sign_share = float(
            (np.sign(boot_contrasts) == np.sign(contrast_val)).mean()
        )
    else:
        sign_share = float((boot_contrasts == 0).mean())

    elapsed = time.time() - t0

    cond_ci = (boot_lo > 0) or (boot_hi < 0)
    cond_cv = (folds_favour >= config.VEG_CV_MIN_FOLDS) and (
        mean_diff > config.VEG_CV_MEAN_GAIN_THRESHOLD
    )
    holds = int(cond_ci) + int(cond_cv)
    if holds == 2:
        outcome = "supported"
    elif holds == 1:
        outcome = "weak or inconclusive"
    else:
        outcome = "not supported"

    text = (
        f"{outcome}: fixed-NDVI gap contrast between bin 1 "
        f"({share_low_total:.1%} of cells, {blocks_low} blocks; {share_low_between:.1%} "
        f"of its cells at NDVI [{p25:.3f}, {p75:.3f}]) and bin 20 "
        f"({share_high_total:.1%} of cells, {blocks_high} blocks; {share_high_between:.1%} "
        f"of its cells at NDVI [{p25:.3f}, {p75:.3f}]) is {contrast_val:+.2f} K "
        f"(model SE {se_contrast:.2f} K, z = {z:+.2f}); "
        f"bootstrap 95% CI [{boot_lo:+.2f}, {boot_hi:+.2f}] over {n_boot_ok} resamples, "
        f"{sign_share:.1%} with the same sign; "
        f"full model beats additive model in {folds_favour} of {config.CV_FOLDS} folds "
        f"with mean gain {mean_diff:+.3f} R2"
    )

    rule = (
        "Conventions chosen after seeing the earlier results: 'supported' requires the "
        "bootstrap 95% interval for the fixed-NDVI contrast to exclude zero AND the full "
        "model to beat the additive model in at least 4 of 5 folds with mean gain > 0.01 "
        "R2; 'weak or inconclusive' means exactly one of those holds; 'not supported' "
        "means neither. The fixed-NDVI correction was made after finding that within-bin "
        "NDVI p25/p75 differ across built bins, so the NDVI range is not common to bins; "
        "the test is exploratory. Model-based SE ignores spatial autocorrelation; the "
        "bootstrap CI accounts for it by resampling 5 km blocks."
    )

    info = {
        "outcome": outcome,
        "p25": p25,
        "p75": p75,
        "share_low_total": share_low_total,
        "share_high_total": share_high_total,
        "share_low_between": share_low_between,
        "share_high_between": share_high_between,
        "blocks_low": blocks_low,
        "blocks_high": blocks_high,
        "contrast": contrast_val,
        "se": se_contrast,
        "z": z,
        "boot_lo": boot_lo,
        "boot_hi": boot_hi,
        "n_boot_ok": n_boot_ok,
        "n_boot": n_boot,
        "sign_share": sign_share,
        "folds_favour": folds_favour,
        "mean_diff": mean_diff,
        "cond_ci": bool(cond_ci),
        "cond_cv": bool(cond_cv),
        "elapsed": elapsed,
    }
    return text, rule, info


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
    veg_text, veg_rule, veg_info = vegetation_result_v3(
        panel, cv["selected_lam"], config.VEG_BOOT_RESPLIES, config.VEG_BOOT_SEED
    )
    print(
        f"{city}: vegetation {veg_info['outcome']} in {veg_info['elapsed']:.0f}s "
        f"(contrast {veg_info['contrast']:+.2f} K, z = {veg_info['z']:+.2f}, "
        f"CI [{veg_info['boot_lo']:+.2f}, {veg_info['boot_hi']:+.2f}] over "
        f"{veg_info['n_boot_ok']}/{veg_info['n_boot']} resamples, "
        f"CV gain {veg_info['mean_diff']:+.3f} in {veg_info['folds_favour']}/5 folds)"
    )

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
