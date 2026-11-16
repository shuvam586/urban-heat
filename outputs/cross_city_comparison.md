# Cross-city comparison: five Indian cities

Assembled from the five `outputs/<city>/summary.md` files (Delhi, Hyderabad, Kolkata, Chennai, Bengaluru). Each city was run independently with the same recipe; nothing is pooled and no city depends on another. All results are associations, not causal effects. Years: 2022, 2023, 2025 (March–May). Grid: 300 m cells, EPSG:7755, 50 km radius. `lst_rel` = cell LST minus the median LST of rural cells (SMOD 11–13) in that city-year.

## 1. City-by-city comparison

| City | Water share | Retained share 2022 / 2023 / 2025 | Rural cells 2022 / 2023 / 2025 |
|---|---|---|---:|
| Delhi | 0.01% (13 cells) | 100.00 / 100.00 / 100.00% | 40,398 / 40,396 / 40,398 |
| Hyderabad | 0.38% (333 cells) | 99.96 / 99.94 / 99.95% | 61,598 / 61,597 / 61,605 |
| Kolkata | 5.76% (5,026 cells) | 99.93 / 99.87 / 98.89% | 13,333 / 13,333 / 13,025 |
| Chennai | 50.37% (43,966 cells) | 89.33 / 99.41 / 97.65% | 18,980 / 20,405 / 20,034 |
| Bengaluru | 0.15% (130 cells) | 99.68 / 99.81 / 99.93% | 49,202 / 49,240 / 49,250 |

Retained share = share of non-water cells with `n_obs >= 3` clear observations (ST_QA_MAX_K = 5 K).

| City | Centre-class median lst_rel (K), 2022 / 2023 / 2025 | Class 22 medians (K), 2022 / 2023 / 2025 | Class 23 medians (K), 2022 / 2023 / 2025 |
|---|---|---|---:|
| Delhi | -0.30 [-0.55,-0.02] / +0.14 [-0.09,+0.35] / +1.01 [+0.80,+1.21] | +2.93 / +1.47 / +1.39 | +0.35 / -0.05 / +0.52 |
| Hyderabad | -2.22 [-2.57,-1.81] / -1.68 [-1.93,-1.44] / -1.98 [-2.22,-1.72] | -0.20 / -0.08 / -0.81 | -0.79 / -0.35 / -0.45 |
| Kolkata | +0.38 [+0.17,+0.62] / +0.20 [-0.15,+0.56] / +0.41 [+0.18,+0.63] | +0.35 / +0.21 / -0.67 | +0.15 / -0.34 / +0.50 |
| Chennai | -0.06 [-0.61,+0.41] / +0.54 [+0.30,+0.81] / +0.04 [-0.19,+0.29] | -0.48 / -0.40 / -0.24 | -0.12 / +0.62 / +0.62 |
| Bengaluru | -1.04 [-1.38,-0.66] / -1.00 [-1.35,-0.67] / -0.94 [-1.19,-0.65] | +0.83 / +0.71 / +0.32 | +0.47 / -0.20 / -0.24 |

Centre medians and 95% bootstrap intervals (5 km blocks) are from each `gradient.csv`; class 22/23 medians are from each `summary.md` class table. Rural class is the reference (0.00 K by construction).

| City | CV R2: NDVI + year / built + year / full | Full-model gain over NDVI + year |
|---|---|---:|
| Delhi | 0.305 / 0.011 / 0.356 | +0.052 |
| Hyderabad | 0.546 / 0.007 / 0.637 | +0.091 |
| Kolkata | 0.332 / 0.230 / 0.461 | +0.129 |
| Chennai | 0.430 / 0.032 / 0.461 | +0.031 |
| Bengaluru | 0.461 / -0.003 / 0.553 | +0.092 |

5 km spatial-block cross-validation, 5 folds, GroupKFold on block id; full model = `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)` fitted on a 10,000-cell random subsample. Kolkata is the only city where built + year has independent CV skill (0.230); everywhere else it is at or near zero.

| City | Total built effect, Fig 2 (1st–99th pct of built) | Direction | Zero crossing | Sparse high-built share (built > 0.4) |
|---|---|---|---|---:|
| Delhi | -2.29 to 1.11 K (built 0.00 to 0.58) | non-monotonic | none inside plotted range | 7.04% |
| Hyderabad | -2.72 to 2.86 K (built 0.00 to 0.50) | falls | near built 0.19 | 3.00% |
| Kolkata | -1.96 to 1.49 K (built 0.00 to 0.49) | rises | near built 0.40 | 3.41% |
| Chennai | -2.86 to 0.17 K (built 0.00 to 0.49) | roughly flat | none inside plotted range | 5.09% |
| Bengaluru | -3.71 to 1.38 K (built 0.00 to 0.50) | falls | near built 0.12 | 3.28% |

Direction per the summary rule: 'roughly flat' if |p50 end − p50 start| < 0.2 K; 'non-monotonic' if the p50 range exceeds 1.5 × |end − start| + 0.2 K; otherwise 'rises'/'falls' from the sign of end − start. Zero crossing = p50 line changes sign inside the plotted range. Descriptive, not a formal test; curves are unsupported where cells are sparse.

| City | Vegetation rule v3.1 outcome | Bin 1 fixed-NDVI coverage | Bin 20 fixed-NDVI coverage | Contrast (K) | z | Bootstrap 95% CI | CV gain | Folds full beats additive |
|---|---|---:|---:|---:|---:|---|---:|---:|
| Delhi | not testable with this data | 61.6% | 0.5% | +5.27 | +9.71 | [+3.32, +6.29] | +0.007 | 4/5 |
| Hyderabad | not testable with this data | 52.2% | 2.0% | +3.10 | +4.86 | [+0.67, +4.31] | +0.014 | 5/5 |
| Kolkata | not testable with this data | 46.9% | 0.0% | +1.55 | +1.94 | [-0.08, +2.23] | +0.037 | 5/5 |
| Chennai | not testable with this data | 48.7% | 0.3% | +4.32 | +4.41 | [+1.05, +5.55] | +0.021 | 5/5 |
| Bengaluru | not testable with this data | 51.4% | 3.3% | +0.19 | +0.36 | [-0.82, +0.97] | +0.013 | 4/5 |

Rule v3.1: if coverage of the fixed NDVI range (city-wide NDVI p25/p75 over non-water cells) is below VEG_MIN_RANGE_SHARE = 5% in either bin 1 or bin 20, the label is "not testable with this data" and the contrast/z/bootstrap interval are exploratory only; otherwise 'supported' requires the bootstrap 95% CI for the contrast to exclude zero AND the full model to beat the additive model in ≥ 4 of 5 folds with mean gain > 0.01 R2; 'weak or inconclusive' means exactly one holds; 'not supported' means neither. All five cities fall below 5% in bin 20, so the fixed-NDVI contrast is extrapolation everywhere and is not a supported test of vegetation moderation.

## 2. Threshold sensitivity: ST_QA_MAX_K = 3 K vs 5 K (Hyderabad and Kolkata)

3 K figures are from `data_3K_backup/` (retained share recomputed from the backup `landsat.parquet`) and git history commits `3b8637e` (Hyderabad run) and `b47a461` (Kolkata run) for centre medians and full-model CV R2. 5 K figures are from the current `outputs/` pipeline. ST_QA_MAX_K = 5 K was chosen post-hoc after the Chennai diagnostic showed that 3 K dropped most otherwise-clear pixels there; it is not a Landsat specification. Chennai's 3 K sample (21 centre cells in 2022; retention 8.39%) was too thin to compare, so only Hyderabad and Kolkata are shown.

| City | Metric | ST_QA_MAX_K = 3 K | ST_QA_MAX_K = 5 K |
|---|---|---|---:|
| Hyderabad | Retained share 2022 / 2023 / 2025 | 96.56 / 95.40 / 95.09% | 99.96 / 99.94 / 99.95% |
| Hyderabad | Centre median lst_rel 2022 / 2023 / 2025 (K) | -2.21 / -2.15 / -2.31 | -2.22 / -1.68 / -1.98 |
| Hyderabad | Full-model CV R2 | 0.582 | 0.637 |
| Kolkata | Retained share 2022 / 2023 / 2025 | 92.24 / 87.56 / 80.38% | 99.93 / 99.87 / 98.89% |
| Kolkata | Centre median lst_rel 2022 / 2023 / 2025 (K) | 0.54 / 0.42 / 0.05 | 0.38 / 0.20 / 0.41 |
| Kolkata | Full-model CV R2 | 0.517 | 0.461 |

Raising the threshold from 3 K to 5 K sharply raised retention (most markedly Chennai: 8.39 / 49.34 / 31.43% at 3 K vs 89.33 / 99.41 / 97.65% at 5 K). For Hyderabad and Kolkata the centre medians and full CV R2 move only modestly, but 3 K is not a defensible default for all cities (Chennai's 2022 centre class had 21 cells).

## 3. Reading across cities

- Centre-class median lst_rel spans -2.22 K (Hyderabad, 2022) to +1.01 K (Delhi, 2025). Hyderabad and Bengaluru both have cooler-than-rural centre classes in all three years, so a cooler centre is not unique to Bengaluru; elevation (~900 m, Bengaluru) or land cover are untested hypotheses, not explanations.
- Full-model CV R2 is 0.356–0.637; NDVI + year carries most of it. Built + year has independent CV skill only in Kolkata (0.230).
- Every city's vegetation result is "not testable with this data" under v3.1 because bin 20 fixed-NDVI coverage is below 5% (0.0%–3.3%); all contrasts are extrapolation and exploratory only.
- Built-effect curves differ in direction (Delhi non-monotonic; Hyderabad and Bengaluru falling; Kolkata rising; Chennai roughly flat) but all are unsupported above built ≈ 0.4 (3–7% of cells).

## Three sentences

Done: I assembled `outputs/cross_city_comparison.md` from the five `summary.md` files (water share, retained share, rural cells, centre medians with intervals, class 22/23 medians, the three CV R2 values, built-effect direction/range/zero crossing, v3.1 vegetation results with bin coverage), added a ST_QA_MAX_K = 3 K vs 5 K threshold-sensitivity table for Hyderabad and Kolkata from `data_3K_backup/` and git history, synced `PLAN.md` to the implemented configuration, marked all five cities reviewed and accepted in `STATUS.md`, and committed everything as "cross-city comparison and PLAN.md sync".
Shows: all five cities are "not testable with this data" under vegetation rule v3.1 (bin 20 fixed-NDVI coverage 0.0%–3.3%, below the 5% threshold); centre-class medians run from -2.22 K (Hyderabad, 2022) to +1.01 K (Delhi, 2025), with Hyderabad and Bengaluru both cooler than rural; raising ST_QA_MAX_K from 3 to 5 K sharply raised retention (Chennai 8.39% to 89.33% in 2022) while moving Hyderabad/Kolkata centre medians and full CV R2 only modestly.
Could be wrong: retained shares and rural counts come from pipeline parquets rather than re-run checks; the 3 K sensitivity figures are taken from superseded backup/git-history outputs and were not re-derived by running; interval spreads reflect the spatial-block bootstrap only; all results are associations, not causal effects, and elevation/land-cover readings of cooler centre classes are untested hypotheses.
