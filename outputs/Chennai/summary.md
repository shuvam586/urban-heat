# Chennai: Urban Heat Summary

## Key summary
- Median `lst_rel` by class: rural is the reference; the centre class is -0.06, 0.54, 0.04 K in 2022/2023/2025. Class 23 has 1,300, 1,435, 1,436 cells in 2022/2023/2025; its medians are -0.12, +0.62, +0.62 K. The 95% bootstrap intervals overlap for all year pairs, so they do not separate the class 23 medians.
- CV R2: NDVI + year 0.430, built + year 0.032, full 0.461; the full model gains 0.031 R2 over NDVI + year.
- Total built effect: `s(built) + te(built, NDVI)` is roughly flat; across the NDVI lines, -2.9 to +0.2 K at built 0.00 and -1.6 to -0.9 K at built 0.49; it does not cross zero inside the plotted range. The curve is unsupported where cells are sparse: 6,308 cells (5.09%) are above built 0.4 and 1,067 (0.86%) above 0.5.
- Built fraction is zero-inflated: 77.4% of cells are below 0.1 and 5.1% are above 0.4 (0.9% above 0.5); the high-built part of the curve is sparse.
- H2 (nonlinearity): the fitted total effect is roughly flat; across the NDVI lines, -2.9 to +0.2 K at built 0.00 and -1.6 to -0.9 K at built 0.49; it does not cross zero inside the plotted range. This is descriptive, not a formal test, and cells above built 0.4 are sparse (6,308, 5.1%).
- H2 (vegetation modification): supported: gap contrast between bin 1 (60.6% cells, 187 blocks) and bin 20 (0.8% cells, 36 blocks) is +2.30 K (SE 0.58 K, z = +3.94; SE ignores spatial autocorrelation); full model beats additive model in 5 of 5 folds with mean gain +0.021 R2.

## Median lst_rel by class (K)
| class | 2022 | 2023 | 2025 |
|---|---:|---:|---:|
| rural | 0.00 | 0.00 | -0.00 |
| suburban | -0.76 | -0.12 | -0.33 |
| semi-dense | -0.48 | -0.40 | -0.24 |
| dense | -0.12 | 0.62 | 0.62 |
| centre | -0.06 | 0.54 | 0.04 |

## Class 23 detail
- 2022: 1,300 cells, median -0.12 K, 95% interval [-0.96, +0.84]
- 2023: 1,435 cells, median +0.62 K, 95% interval [+0.21, +1.16]
- 2025: 1,436 cells, median +0.62 K, 95% interval [+0.05, +1.30]
The 95% bootstrap intervals overlap for all year pairs, so they do not separate the class 23 medians.

## Total built effect (Fig 2)
The fitted total effect is roughly flat; across the NDVI lines, -2.9 to +0.2 K at built 0.00 and -1.6 to -0.9 K at built 0.49; it does not cross zero inside the plotted range.

Rule: direction is 'roughly flat' if |p50 end - p50 start| < 0.2 K, 'non-monotonic' if the p50 range exceeds 1.5 x |end - start| + 0.2 K, otherwise 'rises' or 'falls' from the sign of end - start; a zero crossing is reported when the p50 line changes sign inside the plotted range.

The fitted total effect ranges from -2.86 to 0.17 K over the 1st to 99th percentile of built (0.00 to 0.49). The plot uses 20 built bins, NDVI at its 25th/50th/75th percentile within each bin, year 2022, and a rug of observed built values.

The 95% band is a model-based 95% band for the summed s(built)+te terms using the coefficient covariance, conditional on the selected smoothing.

Only 6,308 cells (5.09%) are above built 0.4 and 1,067 (0.86%) above 0.5; the curve is unsupported where cells are sparse.

## GAM and cross-validation
- Model: `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)`.
- Fit: 10,000 randomly sampled cells, all available years, 28,706 rows.
- Validation: 5 folds, 5000 m spatial blocks, GroupKFold.
- Full-model CV R2: mean 0.461, spread 0.017 (min 0.435, max 0.485).
- Convergence: True.

## Model comparisons (fixed part of step 05, same folds)
| Model | CV R2 mean +/- spread | Selected lam |
|---|---:|---:|
| NDVI + year | 0.430 +/- 0.024 | 10 |
| Built + year | 0.032 +/- 0.008 | 1 |
| Full model | 0.461 +/- 0.017 | 0.1 |

NDVI + year 0.430, built + year 0.032, full 0.461; the full model gains 0.031 R2 over NDVI + year. Rule: the full-model gain is its CV R2 minus the NDVI + year CV R2; no qualitative 'dominant' label is used.

## Built fraction distribution
Built fraction is zero-inflated: 95,964 cells (77.4%) are below 0.1, 6,308 (5.1%) are above 0.4, and 1,067 (0.9%) are above 0.5. The high-built part of the curve is sparse.

## Hypotheses
H2 (nonlinearity): the fitted total effect is roughly flat; across the NDVI lines, -2.9 to +0.2 K at built 0.00 and -1.6 to -0.9 K at built 0.49; it does not cross zero inside the plotted range. This is descriptive, not a formal test, and high-built cells are sparse. H2 (vegetation modification): supported: gap contrast between bin 1 (60.6% cells, 187 blocks) and bin 20 (0.8% cells, 36 blocks) is +2.30 K (SE 0.58 K, z = +3.94; SE ignores spatial autocorrelation); full model beats additive model in 5 of 5 folds with mean gain +0.021 R2. Outcomes are conventions chosen after seeing the results: 'supported' means |z| > 2 for the gap contrast between lowest and highest bins with at least 30 distinct 5 km blocks AND the full model beats the additive model in at least 4 of 5 folds with mean gain > 0.01 R2; 'weak or inconclusive' means exactly one of those holds; 'not supported' means neither holds. The contrast SE is from the coefficient covariance and ignores spatial autocorrelation.

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
Done: I ran steps 01 to 06 for Chennai for 2022, 2023 and 2025, fitting the GAM on a random subsample of 10,000 cells (28,706 rows) with 5 km spatial-block cross-validation.
Shows: Centre-class median `lst_rel` is -0.06, 0.54 and 0.04 K in 2022, 2023 and 2025; NDVI + year 0.430, built + year 0.032, full 0.461; the full model gains 0.031 R2 over NDVI + year; H2 nonlinearity: the fitted total effect is roughly flat; across the NDVI lines, -2.9 to +0.2 K at built 0.00 and -1.6 to -0.9 K at built 0.49; it does not cross zero inside the plotted range; H2 vegetation modification: supported: gap contrast between bin 1 (60.6% cells, 187 blocks) and bin 20 (0.8% cells, 36 blocks) is +2.30 K (SE 0.58 K, z = +3.94; SE ignores spatial autocorrelation); full model beats additive model in 5 of 5 folds with mean gain +0.021 R2.
Could be wrong: The curve is unsupported in sparse high-built bins, the GAM uses a 10,000-cell subsample and smoothing selected at the lower edge, the 95% band is conditional on that smoothing, and all results are associations, not causal effects.
