# Chennai: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is -1.92, -0.34, 0.02 K in 2022/2023/2025. Class 23 has 126, 556, 360 cells in 2022/2023/2025; its medians are -1.17, -0.31, +0.71 K. The 95% bootstrap intervals separate 2022 vs 2023, 2022 vs 2025; the other pairs overlap.
- CV R2: NDVI + year 0.447, built + year -0.041, full 0.487; the full model gains 0.040 R2 over NDVI + year.
- Total built effect: `s(built) + te(built, NDVI)` non-monotonic; across the NDVI lines, -2.3 to +0.2 K at built 0.00 and -2.3 to -1.3 K at built 0.50; it does not cross zero inside the plotted range. The curve is unsupported where cells are sparse: 2,108 cells (5.46%) are above built 0.4 and 411 (1.06%) above 0.5.
- Built fraction is zero-inflated: 78.0% of cells are below 0.1 and 5.5% are above 0.4 (1.1% above 0.5); the high-built part of the curve is sparse.
- H2 (nonlinearity): the fitted total effect non-monotonic; across the NDVI lines, -2.3 to +0.2 K at built 0.00 and -2.3 to -1.3 K at built 0.50; it does not cross zero inside the plotted range. This is descriptive, not a formal test, and cells above built 0.4 are sparse (2,108, 5.5%).
- H2 (vegetation modification): not supported: only 0 of 20 built bins have non-overlapping NDVI p25/p75 95% bands; those bins hold 0.0% of unique non-water cells.

## Median lst_rel by class (K)
| class | 2022 | 2023 | 2025 |
|---|---:|---:|---:|
| rural | -0.00 | 0.00 | 0.00 |
| suburban | -1.79 | -0.61 | -0.68 |
| semi-dense | -2.90 | -1.16 | -1.57 |
| dense | -1.17 | -0.31 | 0.71 |
| centre | -1.92 | -0.34 | 0.02 |

## Class 23 detail
- 2022: 126 cells, median -1.17 K, 95% interval [-2.04, -0.98]
- 2023: 556 cells, median -0.31 K, 95% interval [-0.72, +0.30]
- 2025: 360 cells, median +0.71 K, 95% interval [-0.75, +1.92]
The 95% bootstrap intervals separate 2022 vs 2023, 2022 vs 2025; the other pairs overlap.

## Total built effect (Fig 2)
The fitted total effect non-monotonic; across the NDVI lines, -2.3 to +0.2 K at built 0.00 and -2.3 to -1.3 K at built 0.50; it does not cross zero inside the plotted range.

Rule: direction is 'roughly flat' if |p50 end - p50 start| < 0.2 K, 'non-monotonic' if the p50 range exceeds 1.5 x |end - start| + 0.2 K, otherwise 'rises' or 'falls' from the sign of end - start; a zero crossing is reported when the p50 line changes sign inside the plotted range.

The fitted total effect ranges from -2.55 to 0.24 K over the 1st to 99th percentile of built (0.00 to 0.50). The plot uses 20 built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a model-based 95% band for the summed s(built)+te terms using the coefficient covariance, conditional on the selected smoothing.

Only 2,108 cells (5.46%) are above built 0.4 and 411 (1.06%) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)`.
- Fit: 10,000 randomly sampled cells, all available years, 13,924 rows.
- Validation: 5 folds, 5000 m spatial blocks, GroupKFold.
- Full-model CV R2: mean 0.487, spread 0.059 (min 0.373, max 0.540).
- Convergence: True.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R2 mean +/- spread | Selected lam |
|---|---:|---:|
| NDVI + year | 0.447 +/- 0.044 | 10 |
| Built + year | -0.041 +/- 0.026 | 100 |
| Full model | 0.487 +/- 0.059 | 0.1 |

NDVI + year 0.447, built + year -0.041, full 0.487; the full model gains 0.040 R2 over NDVI + year. Rule: the full-model gain is its CV R2 minus the NDVI + year CV R2; no qualitative 'dominant' label is used.

## Built fraction distribution
Built fraction is zero-inflated: 30,115 cells (78.0%) are below 0.1, 2,108 (5.5%) are above 0.4, and 411 (1.1%) are above 0.5. The high-built part of the curve is sparse.

## Hypotheses
H2 (nonlinearity): the fitted total effect non-monotonic; across the NDVI lines, -2.3 to +0.2 K at built 0.00 and -2.3 to -1.3 K at built 0.50; it does not cross zero inside the plotted range. This is descriptive, not a formal test, and high-built cells are sparse. H2 (vegetation modification): not supported: only 0 of 20 built bins have non-overlapping NDVI p25/p75 95% bands; those bins hold 0.0% of unique non-water cells. Cutoffs are conventions: 'not supported' means at most 2 of 20 built bins separate; 'weak' means the separating bins together hold <5% of unique non-water cells; otherwise the result is 'supported'. A bin separates if the NDVI p25 and p75 95% bands do not overlap.

## Caveats
- The outcome is satellite land surface temperature, not air temperature; heatwave claims are out of scope.
- GHSL classes are 1 km while the grid is 300 m, so class is context rather than a precise per-cell measurement.
- SMOD and BUILT-S are related products, so by-class and pooled results overlap in what they show.
- LST and NDVI come from the same Landsat scenes and share atmosphere and cloud effects; built fraction and NDVI are also negatively correlated, so the interaction term is interpreted cautiously.
- The GAM is fitted to a random subsample of 10,000 cells; CV is on that subsample.
- The smoothing grid was [0.1, 1.0, 10.0, 100.0, 1000.0], and the selected smoothing was 0.1 at the lower edge.
- The 95% band is conditional on the selected smoothing.
- Results are associations only, not causal effects.

## Three sentences
Done: I ran steps 01 to 06 for Chennai for 2022, 2023 and 2025, fitting the GAM on a random subsample of 10,000 cells (13,924 rows) with 5 km spatial-block cross-validation.
Shows: Centre-class median `lst_rel` is -1.92, -0.34 and 0.02 K in 2022, 2023 and 2025; NDVI + year 0.447, built + year -0.041, full 0.487; the full model gains 0.040 R2 over NDVI + year; H2 nonlinearity: the fitted total effect non-monotonic; across the NDVI lines, -2.3 to +0.2 K at built 0.00 and -2.3 to -1.3 K at built 0.50; it does not cross zero inside the plotted range; H2 vegetation modification: not supported: only 0 of 20 built bins have non-overlapping NDVI p25/p75 95% bands; those bins hold 0.0% of unique non-water cells.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a 10,000-cell subsample and smoothing selected at the lower edge, the 95% band is conditional on that smoothing, and all results are associations, not causal effects.
