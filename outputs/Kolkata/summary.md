# Kolkata: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is 0.38, 0.20, 0.41 K in 2022/2023/2025. Class 23 has 4,368, 4,363, 4,317 cells in 2022/2023/2025; its medians are +0.15, -0.34, +0.50 K. The 95% bootstrap intervals separate 2023 vs 2025; the other pairs overlap.
- CV R2: NDVI + year 0.332, built + year 0.230, full 0.461; the full model gains 0.129 R2 over NDVI + year.
- Total built effect: `s(built) + te(built, NDVI)` rises; across the NDVI lines, -2.0 to -1.6 K at built 0.00 and +0.1 to +1.5 K at built 0.49; it crosses zero near built 0.40. The curve is unsupported where cells are sparse: 8,370 cells (3.41%) are above built 0.4 and 1,854 (0.75%) above 0.5.
- Built fraction is zero-inflated: 83.9% of cells are below 0.1 and 3.4% are above 0.4 (0.8% above 0.5); the high-built part of the curve is sparse.
- H2 (nonlinearity): the fitted total effect rises; across the NDVI lines, -2.0 to -1.6 K at built 0.00 and +0.1 to +1.5 K at built 0.49; it crosses zero near built 0.40. This is descriptive, not a formal test, and cells above built 0.4 are sparse (8,370, 3.4%).
- H2 (vegetation modification): not testable with this data: fixed-NDVI gap contrast between bin 1 (57.6% of cells, 344 blocks; 46.9% of its cells at NDVI [0.482, 0.591]) and bin 20 (0.6% of cells, 40 blocks; 0.0% of its cells at NDVI [0.482, 0.591]) is +1.55 K (exploratory only; model SE 0.80 K, z = +1.94); bootstrap 95% CI [-0.08, +2.23] over 200 resamples, 97.0% with the same sign. Coverage of the fixed NDVI range is below 5% in at least one bin, so the contrast is extrapolation and is not a supported test of vegetation moderation. The full model beats the additive model in 5 of 5 folds with mean gain +0.037 R2; this shows the interaction adds a small predictive gain but does not show the direction or cause of any moderation.

## Median lst_rel by class (K)
| class | 2022 | 2023 | 2025 |
|---|---:|---:|---:|
| rural | 0.00 | 0.00 | 0.00 |
| suburban | 0.07 | -0.22 | 0.08 |
| semi-dense | 0.35 | 0.21 | -0.67 |
| dense | 0.15 | -0.34 | 0.50 |
| centre | 0.38 | 0.20 | 0.41 |

## Class 23 detail
- 2022: 4,368 cells, median +0.15 K, 95% interval [-0.17, +0.49]
- 2023: 4,363 cells, median -0.34 K, 95% interval [-0.86, +0.14]
- 2025: 4,317 cells, median +0.50 K, 95% interval [+0.30, +0.71]
The 95% bootstrap intervals separate 2023 vs 2025; the other pairs overlap.

## Total built effect (Fig 2)
The fitted total effect rises; across the NDVI lines, -2.0 to -1.6 K at built 0.00 and +0.1 to +1.5 K at built 0.49; it crosses zero near built 0.40.

Rule: direction is 'roughly flat' if |p50 end - p50 start| < 0.2 K, 'non-monotonic' if the p50 range exceeds 1.5 x |end - start| + 0.2 K, otherwise 'rises' or 'falls' from the sign of end - start; a zero crossing is reported when the p50 line changes sign inside the plotted range.

The fitted total effect ranges from -1.96 to 1.49 K over the 1st to 99th percentile of built (0.00 to 0.49). The plot uses 20 built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a model-based 95% band for the summed s(built)+te terms using the coefficient covariance, conditional on the selected smoothing.

Only 8,370 cells (3.41%) are above built 0.4 and 1,854 (0.75%) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)`.
- Fit: 10,000 randomly sampled cells, all available years, 29,889 rows.
- Validation: 5 folds, 5000 m spatial blocks, GroupKFold.
- Full-model CV R2: mean 0.461, spread 0.030 (min 0.411, max 0.494).
- Convergence: True.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R2 mean +/- spread | Selected lam |
|---|---:|---:|
| NDVI + year | 0.332 +/- 0.030 | 10 |
| Built + year | 0.230 +/- 0.067 | 1000 |
| Full model | 0.461 +/- 0.030 | 0.1 |

NDVI + year 0.332, built + year 0.230, full 0.461; the full model gains 0.129 R2 over NDVI + year. Rule: the full-model gain is its CV R2 minus the NDVI + year CV R2; no qualitative 'dominant' label is used.

## Built fraction distribution
Built fraction is zero-inflated: 206,088 cells (83.9%) are below 0.1, 8,370 (3.4%) are above 0.4, and 1,854 (0.8%) are above 0.5. The high-built part of the curve is sparse.

## Hypotheses
H2 (nonlinearity): the fitted total effect rises; across the NDVI lines, -2.0 to -1.6 K at built 0.00 and +0.1 to +1.5 K at built 0.49; it crosses zero near built 0.40. This is descriptive, not a formal test, and high-built cells are sparse. H2 (vegetation modification): not testable with this data: fixed-NDVI gap contrast between bin 1 (57.6% of cells, 344 blocks; 46.9% of its cells at NDVI [0.482, 0.591]) and bin 20 (0.6% of cells, 40 blocks; 0.0% of its cells at NDVI [0.482, 0.591]) is +1.55 K (exploratory only; model SE 0.80 K, z = +1.94); bootstrap 95% CI [-0.08, +2.23] over 200 resamples, 97.0% with the same sign. Coverage of the fixed NDVI range is below 5% in at least one bin, so the contrast is extrapolation and is not a supported test of vegetation moderation. The full model beats the additive model in 5 of 5 folds with mean gain +0.037 R2; this shows the interaction adds a small predictive gain but does not show the direction or cause of any moderation. Conventions chosen after seeing the earlier results; this is the third version of the rule. 'Supported' requires the bootstrap 95% interval for the fixed-NDVI contrast to exclude zero AND the full model to beat the additive model in at least 4 of 5 folds with mean gain > 0.01 R2; 'weak or inconclusive' means exactly one of those holds; 'not supported' means neither. If coverage of the fixed NDVI range is below 5% in either bin, the contrast is extrapolation and the label is 'not testable with this data'. The fixed-NDVI correction was made after finding that within-bin NDVI p25/p75 differ across built bins, so the NDVI range is not common to bins; the test is exploratory. Model-based SE ignores spatial autocorrelation; the bootstrap CI accounts for it by resampling 5 km blocks.

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
Done: I ran steps 01 to 06 for Kolkata for 2022, 2023 and 2025, fitting the GAM on a random subsample of 10,000 cells (29,889 rows) with 5 km spatial-block cross-validation.
Shows: Centre-class median `lst_rel` is 0.38, 0.20 and 0.41 K in 2022, 2023 and 2025; NDVI + year 0.332, built + year 0.230, full 0.461; the full model gains 0.129 R2 over NDVI + year; H2 nonlinearity: the fitted total effect rises; across the NDVI lines, -2.0 to -1.6 K at built 0.00 and +0.1 to +1.5 K at built 0.49; it crosses zero near built 0.40; H2 vegetation modification: not testable with this data: fixed-NDVI gap contrast between bin 1 (57.6% of cells, 344 blocks; 46.9% of its cells at NDVI [0.482, 0.591]) and bin 20 (0.6% of cells, 40 blocks; 0.0% of its cells at NDVI [0.482, 0.591]) is +1.55 K (exploratory only; model SE 0.80 K, z = +1.94); bootstrap 95% CI [-0.08, +2.23] over 200 resamples, 97.0% with the same sign. Coverage of the fixed NDVI range is below 5% in at least one bin, so the contrast is extrapolation and is not a supported test of vegetation moderation. The full model beats the additive model in 5 of 5 folds with mean gain +0.037 R2; this shows the interaction adds a small predictive gain but does not show the direction or cause of any moderation.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a 10,000-cell subsample and smoothing selected at the lower edge, the 95% band is conditional on that smoothing, and all results are associations, not causal effects.
