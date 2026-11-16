# Bengaluru: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is -1.04, -1.00, -0.94 K in 2022/2023/2025. Class 23 has 1,227, 1,225, 1,229 cells in 2022/2023/2025; its medians are +0.47, -0.20, -0.24 K. The 95% bootstrap intervals overlap for all year pairs, so they do not separate the class 23 medians.
- CV R2: NDVI + year 0.461, built + year -0.003, full 0.553; the full model gains 0.092 R2 over NDVI + year.
- Total built effect: `s(built) + te(built, NDVI)` falls; across the NDVI lines, +1.1 to +1.4 K at built 0.00 and -3.7 to -2.6 K at built 0.50; it crosses zero near built 0.12. The curve is unsupported where cells are sparse: 8,549 cells (3.28%) are above built 0.4 and 2,712 (1.04%) above 0.5.
- Built fraction is zero-inflated: 84.1% of cells are below 0.1 and 3.3% are above 0.4 (1.0% above 0.5); the high-built part of the curve is sparse.
- H2 (nonlinearity): the fitted total effect falls; across the NDVI lines, +1.1 to +1.4 K at built 0.00 and -3.7 to -2.6 K at built 0.50; it crosses zero near built 0.12. This is descriptive, not a formal test, and cells above built 0.4 are sparse (8,549, 3.3%).
- H2 (vegetation modification): not testable with this data: fixed-NDVI gap contrast between bin 1 (66.2% of cells, 352 blocks; 51.4% of its cells at NDVI [0.349, 0.461]) and bin 20 (0.4% of cells, 39 blocks; 3.3% of its cells at NDVI [0.349, 0.461]) is +0.19 K (exploratory only; model SE 0.54 K, z = +0.36); bootstrap 95% CI [-0.82, +0.97] over 200 resamples, 69.0% with the same sign. Coverage of the fixed NDVI range is below 5% in at least one bin, so the contrast is extrapolation and is not a supported test of vegetation moderation. The full model beats the additive model in 4 of 5 folds with mean gain +0.013 R2; this shows the interaction adds a small predictive gain but does not show the direction or cause of any moderation.

## Median lst_rel by class (K)
| class | 2022 | 2023 | 2025 |
|---|---:|---:|---:|
| rural | 0.00 | -0.00 | 0.00 |
| suburban | 0.73 | 0.28 | 0.36 |
| semi-dense | 0.83 | 0.71 | 0.32 |
| dense | 0.47 | -0.20 | -0.24 |
| centre | -1.04 | -1.00 | -0.94 |

## Class 23 detail
- 2022: 1,227 cells, median +0.47 K, 95% interval [-0.12, +0.99]
- 2023: 1,225 cells, median -0.20 K, 95% interval [-0.75, +0.30]
- 2025: 1,229 cells, median -0.24 K, 95% interval [-0.75, +0.34]
The 95% bootstrap intervals overlap for all year pairs, so they do not separate the class 23 medians.

## Total built effect (Fig 2)
The fitted total effect falls; across the NDVI lines, +1.1 to +1.4 K at built 0.00 and -3.7 to -2.6 K at built 0.50; it crosses zero near built 0.12.

Rule: direction is 'roughly flat' if |p50 end - p50 start| < 0.2 K, 'non-monotonic' if the p50 range exceeds 1.5 x |end - start| + 0.2 K, otherwise 'rises' or 'falls' from the sign of end - start; a zero crossing is reported when the p50 line changes sign inside the plotted range.

The fitted total effect ranges from -3.71 to 1.38 K over the 1st to 99th percentile of built (0.00 to 0.50). The plot uses 20 built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a model-based 95% band for the summed s(built)+te terms using the coefficient covariance, conditional on the selected smoothing.

Only 8,549 cells (3.28%) are above built 0.4 and 2,712 (1.04%) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)`.
- Fit: 10,000 randomly sampled cells, all available years, 29,959 rows.
- Validation: 5 folds, 5000 m spatial blocks, GroupKFold.
- Full-model CV R2: mean 0.553, spread 0.031 (min 0.495, max 0.588).
- Convergence: True.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R2 mean +/- spread | Selected lam |
|---|---:|---:|
| NDVI + year | 0.461 +/- 0.036 | 1 |
| Built + year | -0.003 +/- 0.021 | 1 |
| Full model | 0.553 +/- 0.031 | 0.1 |

NDVI + year 0.461, built + year -0.003, full 0.553; the full model gains 0.092 R2 over NDVI + year. Rule: the full-model gain is its CV R2 minus the NDVI + year CV R2; no qualitative 'dominant' label is used.

## Built fraction distribution
Built fraction is zero-inflated: 219,338 cells (84.1%) are below 0.1, 8,549 (3.3%) are above 0.4, and 2,712 (1.0%) are above 0.5. The high-built part of the curve is sparse.

## Hypotheses
H2 (nonlinearity): the fitted total effect falls; across the NDVI lines, +1.1 to +1.4 K at built 0.00 and -3.7 to -2.6 K at built 0.50; it crosses zero near built 0.12. This is descriptive, not a formal test, and high-built cells are sparse. H2 (vegetation modification): not testable with this data: fixed-NDVI gap contrast between bin 1 (66.2% of cells, 352 blocks; 51.4% of its cells at NDVI [0.349, 0.461]) and bin 20 (0.4% of cells, 39 blocks; 3.3% of its cells at NDVI [0.349, 0.461]) is +0.19 K (exploratory only; model SE 0.54 K, z = +0.36); bootstrap 95% CI [-0.82, +0.97] over 200 resamples, 69.0% with the same sign. Coverage of the fixed NDVI range is below 5% in at least one bin, so the contrast is extrapolation and is not a supported test of vegetation moderation. The full model beats the additive model in 4 of 5 folds with mean gain +0.013 R2; this shows the interaction adds a small predictive gain but does not show the direction or cause of any moderation. Conventions chosen after seeing the earlier results; this is the third version of the rule. 'Supported' requires the bootstrap 95% interval for the fixed-NDVI contrast to exclude zero AND the full model to beat the additive model in at least 4 of 5 folds with mean gain > 0.01 R2; 'weak or inconclusive' means exactly one of those holds; 'not supported' means neither. If coverage of the fixed NDVI range is below 5% in either bin, the contrast is extrapolation and the label is 'not testable with this data'. The fixed-NDVI correction was made after finding that within-bin NDVI p25/p75 differ across built bins, so the NDVI range is not common to bins; the test is exploratory. Model-based SE ignores spatial autocorrelation; the bootstrap CI accounts for it by resampling 5 km blocks.

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
Done: I ran steps 01 to 06 for Bengaluru for 2022, 2023 and 2025, fitting the GAM on a random subsample of 10,000 cells (29,959 rows) with 5 km spatial-block cross-validation.
Shows: Centre-class median `lst_rel` is -1.04, -1.00 and -0.94 K in 2022, 2023 and 2025; NDVI + year 0.461, built + year -0.003, full 0.553; the full model gains 0.092 R2 over NDVI + year; H2 nonlinearity: the fitted total effect falls; across the NDVI lines, +1.1 to +1.4 K at built 0.00 and -3.7 to -2.6 K at built 0.50; it crosses zero near built 0.12; H2 vegetation modification: not testable with this data: fixed-NDVI gap contrast between bin 1 (66.2% of cells, 352 blocks; 51.4% of its cells at NDVI [0.349, 0.461]) and bin 20 (0.4% of cells, 39 blocks; 3.3% of its cells at NDVI [0.349, 0.461]) is +0.19 K (exploratory only; model SE 0.54 K, z = +0.36); bootstrap 95% CI [-0.82, +0.97] over 200 resamples, 69.0% with the same sign. Coverage of the fixed NDVI range is below 5% in at least one bin, so the contrast is extrapolation and is not a supported test of vegetation moderation. The full model beats the additive model in 4 of 5 folds with mean gain +0.013 R2; this shows the interaction adds a small predictive gain but does not show the direction or cause of any moderation.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a 10,000-cell subsample and smoothing selected at the lower edge, the 95% band is conditional on that smoothing, and all results are associations, not causal effects.
