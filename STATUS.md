# Status

| City | Steps 01-05 | Step 06 summary | Step 06 check | Notes |
|---|---|---|---|---|
| Hyderabad | pass | written | pass | Approved. Summary regenerated from the city's own results; numbers and conclusions unchanged. |
| Kolkata | pass (first run) | written | pass | Steps 01-05 accepted as a first run. Summary regenerated from Kolkata results: class 23 counts 4,090/3,782/3,605, total built effect rises, vegetation modification weak and limited to bins 17-20. Not yet formally approved. |
| Chennai | pass | written | pass | Unreviewed first run. 2022 is very thin: 3,632 panel rows, 91.6% of cells with `n_obs < 3`, only 21 centre cells. Single Landsat path 142/row 51. Water is 50.4% of the grid. Built + year CV R2 is -0.041; full 0.487, NDVI + year 0.447. Do not treat as a stable city result without review. |

Summary and check_06 are city-generic. No model, figure, setting, limit or numeric output changed.

Kolkata diagnostic: 2025 `n_obs < 3` losses concentrate in path-138-only cells (24.0% vs 0.9% in the both-path overlap), and path 138 has cloud-heavy dates in 2025; the losses track path coverage rather than spreading evenly across footprints.

Chennai caveats: the 50 km circle is 50.4% water, the only Landsat footprint is 142/51, and 2022 has 9 scenes with heavy cloud cover. The 2022 class medians and the 2022-based Fig 2 evaluation are based on a small, selected sample. The `built + year` CV R2 is negative, so built fraction has no independent CV skill in this run.
