import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pygam import LinearGAM, f, s, te

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
Z95 = 1.959963984540054
SUBSAMPLE_CELLS = 10000
SEED = 42
FIG2_BINS = 20


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


def vegetation_result(
    lower_lines, upper_lines, n_valid, bin_cell_counts, total_cells
):
    separated = []
    for i in range(n_valid):
        if not intervals_overlap(
            lower_lines[i, 0],
            upper_lines[i, 0],
            lower_lines[i, 2],
            upper_lines[i, 2],
        ):
            separated.append(i)
    n_sep = len(separated)
    sep_cells = int(bin_cell_counts[separated].sum()) if separated else 0
    sep_share = sep_cells / total_cells if total_cells else 0.0
    rule = (
        "Cutoffs are conventions: 'not supported' means at most 2 of 20 "
        "built bins separate; 'weak' means the separating bins together "
        "hold <5% of unique non-water cells; otherwise the result is "
        "'supported'. A bin separates if the NDVI p25 and p75 95% bands "
        "do not overlap."
    )
    if n_sep <= 2:
        text = (
            f"not supported: only {n_sep} of {n_valid} built bins have "
            "non-overlapping NDVI p25/p75 95% bands; those bins hold "
            f"{sep_share:.1%} of unique non-water cells"
        )
    else:
        first = separated[0] + 1
        last = separated[-1] + 1
        if sep_share < 0.05:
            text = (
                f"weak, limited to bins {first} to {last}: {n_sep} of "
                f"{n_valid} built bins have non-overlapping NDVI p25/p75 "
                "95% bands, but those bins hold only "
                f"{sep_share:.1%} of unique non-water cells"
            )
        else:
            text = (
                f"supported in bins {first} to {last}: {n_sep} of "
                f"{n_valid} built bins have non-overlapping NDVI p25/p75 "
                "95% bands, and those bins hold "
                f"{sep_share:.1%} of unique non-water cells"
            )
    return text, rule, n_sep, separated, sep_share


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
    veg_text, veg_rule, n_sep, separated_bins, veg_share = vegetation_result(
        lower_lines, upper_lines, n_valid, bin_cell_counts, total_cells
    )

    direction_rule = (
        "Rule: direction is 'roughly flat' if |p50 end - p50 start| < 0.2 K, "
        "'non-monotonic' if the p50 range exceeds "
        "1.5 x |end - start| + 0.2 K, otherwise 'rises' or 'falls' from the "
        "sign of end - start; a zero crossing is reported when the p50 line "
        "changes sign inside the plotted range."
    )
    curve_no_period = (
        f"{direction}; across the NDVI lines, "
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
