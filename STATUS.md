# Status

| City | Steps 01-05 | Step 06 summary | Step 06 check | Notes |
|---|---|---|---|---|
| Hyderabad | pass | written | pass | Reviewed and accepted. Rerun under ST_QA_MAX_K = 5. Vegetation rule v3.1: not testable with this data (bin 20 fixed-NDVI coverage 2.0% < 5%; contrast +3.10 K exploratory only; full model beats additive in 5/5 folds, gain +0.014). v2 outcome was weak or inconclusive. |
| Kolkata | pass | written | pass | Reviewed and accepted. Rerun under ST_QA_MAX_K = 5. Vegetation rule v3.1: not testable with this data (bin 20 fixed-NDVI coverage 0.0% < 5%; contrast +1.55 K exploratory only; full model beats additive in 5/5 folds, gain +0.037). v2 outcome was supported. |
| Chennai | pass | written | pass | Reviewed and accepted. Rerun under ST_QA_MAX_K = 5. Vegetation rule v3.1: not testable with this data (bin 20 fixed-NDVI coverage 0.3% < 5%; contrast +4.32 K exploratory only; full model beats additive in 5/5 folds, gain +0.021). v2 outcome was supported. |
| Delhi | pass | written | pass | Reviewed and accepted. Rerun under ST_QA_MAX_K = 5. Vegetation rule v3.1: not testable with this data (bin 20 fixed-NDVI coverage 0.5% < 5%; contrast +5.27 K exploratory only; full model beats additive in 4/5 folds, gain +0.007). |
| Bengaluru | pass | written | pass | Reviewed and accepted. Rerun under ST_QA_MAX_K = 5. Vegetation rule v3.1: not testable with this data (bin 20 fixed-NDVI coverage 3.3% < 5%; contrast +0.19 K exploratory only; full model beats additive in 4/5 folds, gain +0.013). Centre class cooler than rural (-1.04/-1.00/-0.94 K), consistent with ~900 m elevation but an untested hypothesis; Hyderabad also has a cooler centre class. Retention 99.68/99.81/99.93% (277/168/59 cells dropped for n_obs < 3). |

Decision: ST_QA_MAX_K = 5 for ALL cities. It was chosen post-hoc after seeing a diagnostic in Chennai (the original 3 K default was an ungrounded user choice, not a Landsat specification). All cities are to be processed under 5 K without per-city tuning.

Vegetation rule v2 (post-hoc convention):
- Moderation is evaluated via: (1) gap contrast between lowest and highest bins with >= 30 distinct 5 km blocks (|z| > 2, using coefficient covariance), AND (2) full model beats additive model in >= 4 of 5 folds with mean gain > 0.01 R2.
- Outcomes:
  - Hyderabad: weak or inconclusive (z = +0.27, CV gain +0.014 across 5/5 folds).
  - Kolkata: supported (z = -2.38, CV gain +0.037 across 5/5 folds).
  - Chennai: supported (z = +3.94, CV gain +0.021 across 5/5 folds).

Summary and check_06 are city-generic. No model, figure, setting, limit or numeric output changed. The summary wording was corrected to "the fitted total effect is non-monotonic"; check_06 was updated to accept that grammar. Only the Chennai summary text changed.

Chennai data adequacy diagnostic (scratchpad only, 300 m non-water cells; pipeline `n_obs` is the mean valid 30 m observation count per cell):

| City | Year | QA-only median `n_obs` | QA-only share `< 3` | ST_QA <= 3 K median | ST_QA <= 3 K share `< 3` | ST_QA <= 5 K median | ST_QA <= 5 K share `< 3` |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chennai | 2022 | 5.12 | 1.83% | 1.93 | 91.61% | 4.00 | 10.67% |
| Chennai | 2023 | 5.97 | 0.002% | 2.99 | 50.66% | 5.00 | 0.59% |
| Chennai | 2025 | 6.70 | 0.097% | 2.00 | 68.57% | 5.90 | 2.35% |
| Hyderabad | 2022 | 9.00 | 0.003% | 6.00 | 3.44% | 8.29 | 0.04% |
| Hyderabad | 2023 | 7.82 | 0.003% | 5.06 | 4.60% | 7.00 | 0.06% |
| Hyderabad | 2025 | 9.00 | 0.001% | 7.29 | 4.91% | 9.00 | 0.05% |
| Kolkata | 2022 | 8.04 | 0.000% | 5.00 | 7.75% | 7.33 | 0.07% |
| Kolkata | 2023 | 9.00 | 0.001% | 4.85 | 12.42% | 8.55 | 0.13% |
| Kolkata | 2025 | 7.06 | 0.040% | 4.00 | 19.58% | 6.00 | 1.11% |

The ST_QA <= 5 K column is exploration only, not a proposed setting. With QA_PIXEL masking alone, essentially every non-water cell clears `n_obs < 3` in all three cities; the Chennai deficit appears only when `ST_QA <= 3 K` is applied. In Chennai, 6 of 9 scenes in 2022 and 6 of 12 in 2023 lose more than 90% of otherwise-clear pixel area to the ST_QA filter; the scene-median ST_QA is 2.7-6.0 K in 2022 and 2.0-6.3 K in 2023.

Chennai path 142/row 51 fully covers the 50 km circle. No non-water cell is within 2 km of the footprint edge; the minimum edge distance is 35.4 km. Retention after `n_obs < 3` at ST_QA_MAX_K = 5: Hyderabad 99.96/99.94/99.95%, Kolkata 99.93/99.87/98.89%, Chennai 89.33/99.41/97.65%. The 3 K retention figures (Hyderabad 96.56/95.40/95.09%, Kolkata 92.24/87.56/80.38%, Chennai 8.39/49.34/31.43%) are superseded. The pipeline `n_obs` is a mean 30 m count per 300 m cell, not the number of scenes with a valid pixel; any-valid-cell shares are more optimistic (Chennai 2022 ST_QA <= 3 K: 74.4% versus 91.6%).

Kolkata diagnostic: 2025 `n_obs < 3` losses concentrate in path-138-only cells (24.0% vs 0.9% in the both-path overlap), and path 138 has cloud-heavy dates in 2025; the losses track path coverage rather than spreading evenly across footprints.

Chennai caveats: the 50 km circle is 50.4% water, the only Landsat footprint is 142/51, and 2022 has 9 scenes with heavy cloud cover. The 2022 class medians and the 2022-based Fig 2 evaluation are based on a small, selected sample. The `built + year` CV R2 is negative, so built fraction has no independent CV skill in this run.

Vegetation rule v3.1 (fixed-NDVI contrast + spatial-block bootstrap with a coverage condition; convention chosen after seeing earlier results; this is the third version of the rule; exploratory):
- If coverage of the fixed NDVI range is below VEG_MIN_RANGE_SHARE (5%) in either the lowest or highest built bin, the label is "not testable with this data" and the contrast/z/bootstrap interval are reported as exploratory only; otherwise 'supported' requires the bootstrap 95% CI for the contrast to exclude zero AND the full model to beat the additive model in at least 4 of 5 folds with mean gain > 0.01 R2; 'weak or inconclusive' means exactly one of those holds; 'not supported' means neither.
- Fixed NDVI values are the city-wide p25/p75 of per-cell mean NDVI over non-water cells, so the same NDVI range is used in every built bin (v2 used within-bin quantiles, so the NDVI range differed between bins).
- Contrast = (gap at bin 20) minus (gap at bin 1), gap = total effect at NDVI p75 minus total effect at NDVI p25. Model-based SE ignores spatial autocorrelation; bootstrap CI resamples 5 km blocks with replacement and refits the full GAM with selected smoothing fixed.

| City | NDVI p25/p75 | Bin 1 share in range | Bin 20 share in range | Contrast (K) | z | Bootstrap 95% CI | CV gain | folds | Outcome |
|---|---|---|---|---|---|---|---|---|---|
| Hyderabad | 0.304 / 0.416 | 52.2% | 2.0% | +3.10 | +4.86 | [+0.67, +4.31] | +0.014 | 5/5 | not testable with this data |
| Kolkata | 0.482 / 0.591 | 46.9% | 0.0% | +1.55 | +1.94 | [-0.08, +2.23] | +0.037 | 5/5 | not testable with this data |
| Chennai | 0.360 / 0.508 | 48.7% | 0.3% | +4.32 | +4.41 | [+1.05, +5.55] | +0.021 | 5/5 | not testable with this data |
| Delhi | 0.244 / 0.343 | 61.6% | 0.5% | +5.27 | +9.71 | [+3.32, +6.29] | +0.007 | 4/5 | not testable with this data |
| Bengaluru | 0.349 / 0.461 | 51.4% | 3.3% | +0.19 | +0.36 | [-0.82, +0.97] | +0.013 | 4/5 | not testable with this data |

- All five cities with v3.1 results (Hyderabad, Kolkata, Chennai, Delhi, Bengaluru) have fewer than 5% of bin-20 cells in the fixed NDVI range (Hyderabad 2.0%, Kolkata 0.0%, Chennai 0.3%, Delhi 0.5%, Bengaluru 3.3%). Hyderabad was not flagged in the earlier v3 report but is now covered by the same condition. The contrast is extrapolation in every city and is not a supported test of vegetation moderation.
- Sign changed for Kolkata relative to v2 (-1.05 K) because fixed NDVI values differ from within-bin quantiles; this is the expected effect of the fix.

Delhi diagnostic (report only):
- Scenes (Earth Engine metadata WRS_PATH/WRS_ROW/CLOUD_COVER): 2022 = 35, 2023 = 30, 2025 = 36; paths 146/40, 146/41, 147/40 cover the circle (scenes per month Mar/Apr/May = 11/12/12, 12/8/10, 12/12/12).
- Path coverage: 44,566 cells single-path (median n_obs 6.98–11.00) and 42,701 dual-path (median n_obs 13.00–20.45); n_obs < 3 share is 0.00% in every group and year; no cell is uncovered.
- gradient.csv (committed): centre median lst_rel −0.30 / +0.14 / +1.01 K in 2022/2023/2025; class 22 median +2.93 / +1.47 / +1.39 K (all bootstrap intervals exclude zero).
- Centre lst_rel change: 2022→2023 driven mainly by the rural reference (rural LST 313.90→309.74 K vs centre 313.60→309.88 K); 2023→2025 driven mainly by the centre itself (rural 309.74→311.04 K vs centre 309.88→312.06 K). Diagnostic only, not a causal claim.
- Class 22: 869 cells in 61 distinct 5 km blocks; three largest blocks hold 15.2% of cells (max block 5.9%), so not driven by a few localities; per-year median lst_rel +2.93 / +1.47 / +1.39 K.

RQ1 rural references (all five cities, reviewed and accepted):
- 07_rq1_references.py and tests/check_07_rq1_references.py ran via Git Bash for Hyderabad, Kolkata, Chennai, Delhi, and Bengaluru; all five checks passed. outputs/<city>/rq1_references.csv and fig4_rq1_references.png written for every city; combined table at outputs/rq1_cross_city_references.md. No Earth Engine calls; only existing grid.parquet/panel.parquet used.
- Reference coverage (cells / distinct 5 km blocks), 2022/2023/2025:
  Ref_A: Delhi 40,398/40,396/40,398 (301/301/301), Hyderabad 61,598/61,597/61,605 (331/331/331), Kolkata 13,333/13,333/13,025 (261/262/259), Chennai 18,980/20,405/20,034 (161/162/162), Bengaluru 49,202/49,240/49,250 (328/328/328).
  Ref_B: Delhi 20,903/20,902/20,903 (287/287/287), Hyderabad 28,993/28,999/29,009 (319/319/319), Kolkata 3,614/3,611/3,504 (165/165/165), Chennai 7,887/8,405/8,282 (148/148/148), Bengaluru 16,707/16,733/16,734 (293/293/293).
  Ref_C: Delhi 18,845/19,017/18,933 (295/293/297), Hyderabad 29,946/29,979/29,870 (326/325/325), Kolkata 6,483/6,393/6,340 (232/233/231), Chennai 9,014/9,704/9,529 (153/155/156), Bengaluru 23,188/23,235/23,135 (322/325/320).
- All reference groups exceed 200 cells and 30 distinct 5 km blocks in every city/year (minimum Kolkata Ref_B 2025: 3,504 cells / 165 blocks).
- Reference median LST differences versus Ref_A (K), from panel.parquet: Ref_C − Ref_A ranges from −0.561 K (Kolkata 2023) to −2.176 K (Bengaluru 2025); Ref_B − Ref_A ranges from −0.604 K (Bengaluru 2025) to +0.145 K (Hyderabad 2025). Ref_C is therefore COOLER than Ref_A (not hotter). Because `lst_rel = cell_LST − ref_LST`, subtracting a cooler reference shifts urban medians upward.
- Centre class 30 median lst_rel (K), 2022/2023/2025: Ref_A centre -0.30/+0.14/+1.01 (Delhi), -2.22/-1.68/-1.98 (Hyderabad), +0.38/+0.20/+0.41 (Kolkata), -0.06/+0.54/+0.04 (Chennai), -1.04/-1.00/-0.94 (Bengaluru).
- Centre sign flips under Ref_C: Hyderabad 2023 (-1.68 -> +0.14), Chennai 2022 (-0.06 -> +1.91), Bengaluru all three years (-1.04/-1.00/-0.94 -> +0.69/+0.33/+1.23); under Ref_B: Delhi 2022 (-0.30 -> +0.22). Kolkata shows no sign change under any reference. Associations only, not causal.

Pending: none for the main pipeline. All five cities (Delhi, Hyderabad, Kolkata, Chennai, Bengaluru) have been run, reviewed and accepted under ST_QA_MAX_K = 5 and vegetation rule v3.1; all five are "not testable with this data" for vegetation moderation (bin 20 fixed-NDVI coverage below 5%). RQ1 rural references are complete and reviewed for all five cities. The five-city comparison table is at outputs/cross_city_comparison.md; the RQ1 sensitivity table is at outputs/rq1_cross_city_references.md. PLAN.md is synced to the implemented code and decisions (years 2022/2023/2025, water rule, ST_QA_MAX_K = 5 post-hoc, MIN_CLEAR_OBS = 3, MAX_MISSING_LST_SHARE = 0.10, drop low-n_obs cells in step 03, total built effect Fig 2, extrapolation mask Fig 3, three-model CV comparison, H2 rule v3.1 with VEG_MIN_RANGE_SHARE = 0.05).
