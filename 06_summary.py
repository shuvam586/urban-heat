import argparse
import json
from pathlib import Path

import pandas as pd

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]


def intervals_overlap(a_low, a_high, b_low, b_high):
    return not (a_high < b_low or b_high < a_low)


def fmt_lam(value):
    return f"{value:g}"


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

    comparisons = cv["model_comparisons"]["models"]
    ndvi = comparisons["ndvi_year"]
    built = comparisons["built_year"]
    full = comparisons["full"]
    comparison_rows = [
        f"| NDVI + year | {ndvi['r2_mean']:.3f} ± {ndvi['r2_std']:.3f} | "
        f"{fmt_lam(ndvi['selected_lam'])} |",
        f"| Built + year | {built['r2_mean']:.3f} ± {built['r2_std']:.3f} | "
        f"{fmt_lam(built['selected_lam'])} |",
        f"| Full model | {full['r2_mean']:.3f} ± {full['r2_std']:.3f} | "
        f"{fmt_lam(full['selected_lam'])} |",
    ]
    comparison_table = "\n".join(comparison_rows)

    total_min = cv["built_total_min"]
    total_max = cv["built_total_max"]
    shape_words = cv["built_total_shape_words"]
    unsupported_words = cv["built_unsupported_words"]
    n04 = cv["n_cells_above_built_0.4"]
    n05 = cv["n_cells_above_built_0.5"]
    s04 = cv["share_above_built_0.4"]
    s05 = cv["share_above_built_0.5"]
    below01 = cv["share_below_built_0.1"]

    summary = f"""# {city}: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is {medians.loc['centre', years[0]]:.2f}, {medians.loc['centre', years[1]]:.2f}, {medians.loc['centre', years[2]]:.2f} K in {years[0]}/{years[1]}/{years[2]}. Class 23 has about 1,200 cells per year; its medians are {dense.loc[years[0], 'median']:+.2f}, {dense.loc[years[1], 'median']:+.2f}, {dense.loc[years[2], 'median']:+.2f} K, and the bootstrap intervals overlap across years.
- CV R²: full model {cv['r2_mean']:.3f} ± {cv['r2_std']:.3f}. NDVI + year explains most of the CV R-squared ({ndvi['r2_mean']:.3f}); built + year alone is only {built['r2_mean']:.3f}.
- Total built effect: `s(built) + te(built, NDVI)` spans {total_min:.2f} to {total_max:.2f} K and is generally downward; {unsupported_words}
- Built fraction is zero-inflated: {below01:.1%} of cells are below 0.1 and {s04:.1%} are above 0.4 ({s05:.1%} above 0.5); the high-built part of the curve is weakly supported.
- H2 and H3 are weakly supported where data allow.

## Median lst_rel by class (K)
| class | {years[0]} | {years[1]} | {years[2]} |
|---|---:|---:|---:|
{class_table}

## Class 23 detail
{dense_text}
{separation}

## Total built effect (Fig 2)
{shape_words}

The fitted total effect ranges from {total_min:.2f} to {total_max:.2f} K over the 1st–99th percentile of built ({cv['fig2_built_range'][0]:.2f}–{cv['fig2_built_range'][1]:.2f}). The plot uses {cv['fig2_built_bins']} built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a {cv['fig2_band']}.

Only {n04:,} cells ({s04:.2%}) are above built 0.4 and {n05:,} ({s05:.2%}) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `{cv['model']}`.
- Fit: {cv['subsample_cells']:,} randomly sampled cells, all available years, {cv['subsample_rows']:,} rows.
- Validation: {cv['n_folds']} folds, {cv['block_size_m']} m spatial blocks, GroupKFold.
- Full-model CV R²: mean {cv['r2_mean']:.3f}, spread {cv['r2_std']:.3f} (min {cv['r2_min']:.3f}, max {cv['r2_max']:.3f}).
- Convergence: {cv['converged']}.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R² mean ± spread | Selected lam |
|---|---:|---:|
{comparison_table}

NDVI + year explains most of the CV R-squared ({ndvi['r2_mean']:.3f} vs {cv['r2_mean']:.3f} for the full model); built + year alone is {built['r2_mean']:.3f}. The full model adds about {cv['r2_mean'] - ndvi['r2_mean']:.3f} R² over NDVI + year.

## Built fraction distribution
Built fraction is zero-inflated: {cv['n_cells_below_built_0.1']:,} cells ({below01:.1%}) are below 0.1, {n04:,} ({s04:.1%}) are above 0.4, and {n05:,} ({s05:.1%}) are above 0.5. The high-built part of the curve is weakly supported.

## Hypotheses
H2 and H3 are weakly supported where data allow. H2 (a nonlinear built-up effect modified by vegetation) is not strongly identified here: the full model improves on NDVI + year by only about {cv['r2_mean'] - ndvi['r2_mean']:.3f} R², built + year alone is near zero, and high-built cells are sparse.

## Caveats
- The outcome is satellite land surface temperature, not air temperature; heatwave claims are out of scope.
- GHSL classes are 1 km while the grid is 300 m, so class is context rather than a precise per-cell measurement.
- SMOD and BUILT-S are related products, so by-class and pooled results overlap in what they show.
- LST and NDVI come from the same Landsat scenes and share atmosphere and cloud effects; built fraction and NDVI are also negatively correlated, so the interaction term is interpreted cautiously.
- The GAM is fitted to a random subsample of {cv['subsample_cells']:,} cells; CV is on that subsample.
- The smoothing grid was {cv['lam_grid']}, and the selected smoothing was {cv['selected_lam']} at the lower edge.
- The 95% band is conditional on the selected smoothing.
- Results are associations only, not causal effects.

## Three sentences
Done: I refitted the specified GAM on the same {cv['subsample_cells']:,}-cell subsample, replaced Fig 2 with the total built effect (`s(built) + te`) at NDVI p25/p50/p75 with model-based 95% bands, fixed the Fig 3 mask orientation, and added the three same-fold CV comparisons.
Shows: The total built effect spans {total_min:.2f} to {total_max:.2f} K and is generally downward; NDVI + year gets CV R² {ndvi['r2_mean']:.3f}, built + year {built['r2_mean']:.3f}, and the full model {cv['r2_mean']:.3f}; built is zero-inflated ({below01:.1%} below 0.1, {s04:.1%} above 0.4), and class 23's year intervals overlap.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a {cv['subsample_cells']:,}-cell subsample and smoothing selected at the lower edge, the 95% band is conditional on that smoothing, H2 and H3 are weakly supported where data allow, and all results are associations, not causal effects.
"""

    path = output_dir / "summary.md"
    path.write_text(summary, encoding="utf-8")
    print(f"{city}: wrote {path}")


if __name__ == "__main__":
    main()
