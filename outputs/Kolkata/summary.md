# Kolkata: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is 0.54, 0.42, 0.05 K in 2022/2023/2025. Class 23 has about 1,200 cells per year; its medians are +0.40, +0.15, +0.54 K, and the bootstrap intervals overlap across years.
- CV R²: full model 0.517 ± 0.023. NDVI + year explains most of the CV R-squared (0.459); built + year alone is only 0.193.
- Total built effect: `s(built) + te(built, NDVI)` spans -1.85 to 0.96 K and is generally downward; The curve is unsupported where cells are sparse: 7,549 cells (3.53%) are above built 0.4 and 1,722 (0.80%) above 0.5.
- Built fraction is zero-inflated: 83.5% of cells are below 0.1 and 3.5% are above 0.4 (0.8% above 0.5); the high-built part of the curve is weakly supported.
- H2 (nonlinearity): the total effect declines roughly steadily with a mild flattening above about 0.4, not formally tested, and sparse above 0.4.
- H2 (vegetation modification): not supported, because the NDVI p25, p50 and p75 curves have overlapping 95% bands over almost the whole range.

## Median lst_rel by class (K)
| class | 2022 | 2023 | 2025 |
|---|---:|---:|---:|
| rural | 0.00 | 0.00 | 0.00 |
| suburban | 0.12 | -0.10 | 0.05 |
| semi-dense | 0.04 | 0.28 | 0.01 |
| dense | 0.40 | 0.15 | 0.54 |
| centre | 0.54 | 0.42 | 0.05 |

## Class 23 detail
- 2022: 4,090 cells, median +0.40 K, 95% interval [+0.06, +0.74]
- 2023: 3,782 cells, median +0.15 K, 95% interval [-0.21, +0.56]
- 2025: 3,605 cells, median +0.54 K, 95% interval [+0.17, +0.91]
The 95% bootstrap intervals overlap for all year pairs, so they do not separate the class 23 medians.

## Total built effect (Fig 2)
The total built effect is generally downward: from -1.8--0.9 K at built 0.00, without crossing zero inside the plotted range, to -0.1-1.0 K at built 0.49; the three NDVI lines are close at low built and diverge at high built, with the highest-NDVI line the most negative.

The fitted total effect ranges from -1.85 to 0.96 K over the 1st–99th percentile of built (0.00–0.49). The plot uses 20 built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a model-based 95% band for the summed s(built)+te terms using the coefficient covariance, conditional on the selected smoothing.

Only 7,549 cells (3.53%) are above built 0.4 and 1,722 (0.80%) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)`.
- Fit: 10,000 randomly sampled cells, all available years, 27,563 rows.
- Validation: 5 folds, 5000 m spatial blocks, GroupKFold.
- Full-model CV R²: mean 0.517, spread 0.023 (min 0.486, max 0.549).
- Convergence: True.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R² mean ± spread | Selected lam |
|---|---:|---:|
| NDVI + year | 0.459 ± 0.040 | 1 |
| Built + year | 0.193 ± 0.066 | 10 |
| Full model | 0.517 ± 0.023 | 0.1 |

NDVI + year explains most of the CV R-squared (0.459 vs 0.517 for the full model); built + year alone is 0.193. The full model adds about 0.059 R² over NDVI + year.

## Built fraction distribution
Built fraction is zero-inflated: 178,650 cells (83.5%) are below 0.1, 7,549 (3.5%) are above 0.4, and 1,722 (0.8%) are above 0.5. The high-built part of the curve is weakly supported.

## Hypotheses
H2 (nonlinearity): the total effect declines roughly steadily with a mild flattening above about 0.4, not formally tested, and sparse above 0.4. H2 (vegetation modification): not supported, because the NDVI p25, p50 and p75 curves have overlapping 95% bands over almost the whole range. The full model improves on NDVI + year by only about 0.059 R², built + year alone is near zero, and high-built cells are sparse.

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
Done: I ran steps 01 to 06 for Kolkata for 2022, 2023 and 2025, fitting the GAM on a random subsample of 10,000 cells (27,563 rows) with 5 km spatial-block cross-validation.
Shows: Centre-class median `lst_rel` is 0.54, 0.42 and 0.05 K in 2022, 2023 and 2025; CV R² is 0.459 for NDVI + year, 0.193 for built + year and 0.517 for the full model; H2 nonlinearity: the total effect declines roughly steadily with a mild flattening above about 0.4, not formally tested, and sparse above 0.4; H2 vegetation modification: not supported, because the NDVI p25, p50 and p75 curves have overlapping 95% bands over almost the whole range.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a 10,000-cell subsample and smoothing selected at the lower edge, the 95% band is conditional on that smoothing, and all results are associations, not causal effects.
