# Status

| City | Steps 01-05 | Step 06 summary | Step 06 check | Notes |
|---|---|---|---|---|
| Hyderabad | pass | written | pass | Approved. Summary regenerated from the city's own results; numbers and conclusions unchanged. |
| Kolkata | pass (first run) | written | pass | Steps 01-05 accepted as a first run. Summary regenerated from Kolkata results: class 23 counts 4,090/3,782/3,605, total built effect rises, vegetation modification weak and limited to bins 17-20. Not yet formally approved. |
| Chennai | pass | written | pass | Unreviewed first run. 2022 is very thin: 3,632 panel rows, 91.6% of cells with `n_obs < 3`, only 21 centre cells. Single Landsat path 142/row 51. Water is 50.4% of the grid. Built + year CV R2 is -0.041; full 0.487, NDVI + year 0.447. Do not treat as a stable city result without review. The 2022 `n_obs < 3` loss is caused by the `ST_QA <= 3 K` filter, not QA_PIXEL cloud masking. |

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

Chennai path 142/row 51 fully covers the 50 km circle. No non-water cell is within 2 km of the footprint edge; the minimum edge distance is 35.4 km. Retention after `n_obs < 3` is confirmed: Hyderabad 96.56/95.40/95.09%, Kolkata 92.24/87.56/80.38%, Chennai 8.39/49.34/31.43%. The pipeline `n_obs` is a mean 30 m count per 300 m cell, not the number of scenes with a valid pixel; any-valid-cell shares are more optimistic (Chennai 2022 ST_QA <= 3 K: 74.4% versus 91.6%).

Kolkata diagnostic: 2025 `n_obs < 3` losses concentrate in path-138-only cells (24.0% vs 0.9% in the both-path overlap), and path 138 has cloud-heavy dates in 2025; the losses track path coverage rather than spreading evenly across footprints.

Chennai caveats: the 50 km circle is 50.4% water, the only Landsat footprint is 142/51, and 2022 has 9 scenes with heavy cloud cover. The 2022 class medians and the 2022-based Fig 2 evaluation are based on a small, selected sample. The `built + year` CV R2 is negative, so built fraction has no independent CV skill in this run.
