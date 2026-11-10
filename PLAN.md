# Urban Heat in Five Indian Cities: Simplified Plan

One city, one notebook, repeated five times. Each city is a self-contained run of the same recipe. Nothing is pooled and no city depends on another, so the cities can be run in any order or in parallel.

## Question and hypotheses

**Question:** In each city, how does March–May land surface temperature (LST) change along the GHSL urban–rural ladder, and how does it depend on built-up fraction and vegetation?

- **H1:** LST relative to rural land rises along the ladder, though it may be flat or negative by day where rural land is bare.
- **H2:** The built-up–LST relationship is nonlinear, and vegetation changes it.

Results are associations only, not causal effects.

## Fixed settings

These are identical for every city and are never edited per city.

| Setting | Value |
| :-- | :-- |
| Cities | Delhi, Kolkata, Chennai, Bengaluru, Hyderabad |
| Area | 50 km radius around the city centre |
| Grid | 300 m cells, EPSG:7755 |
| Years | 2019, 2022, 2025 |
| Season | March–May median composite |
| Ladder | SMOD 2020: rural (11–13), suburban (21), semi-dense (22), dense (23), centre (30); water excluded |
| Built-up measure | GHS-BUILT-S 2020 built fraction |
| Vegetation | Landsat NDVI |
| Outcome | `lst_rel` = cell LST minus the median LST of rural cells in that city-year |
| Data | SMOD, BUILT-S, Landsat 8/9 L2, JRC water mask. Nothing else. |

## The recipe

One parameterised notebook, `city_analysis.ipynb`, with `CITY = "..."` in the first cell.

| Step | What it does | Output |
| :-- | :-- | :-- |
| 1. Grid | Build the 300 m grid and attach SMOD class and built fraction | Map of classes |
| 2. Landsat | Extract LST and NDVI per cell for the 3 years; mask clouds and water | Map of mean LST |
| 3. Table | Join into one table and compute `lst_rel`. Stop and flag if the city has fewer than 200 rural cells per year | Table of cell counts per class |
| 4. Gradient | `lst_rel` by ladder class, with spatial-block bootstrap intervals (5 km blocks) | Boxplot by class (Fig 1) |
| 5. Model | One GAM: `lst_rel ~ s(built) + s(NDVI) + te(built, NDVI)`, scored with 5 km spatial-block cross-validation | Built-up curve (Fig 2), interaction plot (Fig 3), CV R² |
| 6. Summary | Auto-fill a 5-line summary: median `lst_rel` by class, CV R², shape of the curve, caveats | `summary.md` |

Everything is saved to `outputs/<city>/`: one table, three figures, one summary. That is 6 steps and about 10 cells, and each step ends in something you can look at.

## Combining the cities

This is the only cross-city step. Paste the five `summary.md` files into one comparison table (class medians, CV R², curve shape) and compare the cities by reading it. Do not fit pooled models, leave-one-city-out checks or hierarchical models.

## Rules for the agent

1. Do not add datasets, metrics, models, years or checks that are not listed. Ask first.
2. Run Hyderabad, show the six outputs, and wait. Only then run the other four with the same notebook.
3. Do not edit the notebook per city. If a city needs special handling, flag it in `summary.md` instead.
4. Every result comes with three sentences: what was done, what it shows, what could be wrong.
5. No gates, manifests, decision logs or extra folders. The repo is `city_analysis.ipynb`, `config.py` and `outputs/`.

## Deliberately left out

These are possible later papers:

- Built-up history and trajectory
- Comparing built-up metrics (NDBI, Dynamic World, WorldCover)
- Alternative rural references
- Thresholds
- Leave-one-year-out or leave-one-city-out validation
- Population, building height, climate covariates and night LST

## Limitations to keep in mind

- The outcome is satellite land surface temperature, not air temperature, so heatwave claims are out of scope.
- GHSL classes are 1 km while the grid is 300 m, so class is context rather than a precise per-cell measurement.
- SMOD and BUILT-S are related products, so by-class and pooled results will overlap in what they show.

## Agent-ready spec: repo layout

The agent builds and runs scripts, not notebooks. Each script takes `--city`, reads only `config.py`, and writes only to its own output path.

```text
config.py            # city centres, years, season, radius, dataset IDs, bands, scale factors
requirements.txt     # pinned: earthengine-api, pygam, geopandas, pandas, pyarrow, scikit-learn
00_smoke_test.py     # EE init + read one SMOD pixel and one Landsat pixel, print OK
01_grid_attrs.py     # -> data/<city>/grid.parquet
02_landsat.py        # -> data/<city>/landsat.parquet
03_panel.py          # join, mask, lst_rel -> data/<city>/panel.parquet
04_gradient.py       # -> outputs/<city>/fig1_gradient.png, gradient.csv
05_gam.py            # -> outputs/<city>/fig2_builtup.png, fig3_interaction.png, cv.json
06_summary.py        # -> outputs/<city>/summary.md
run_city.sh          # runs 01-06 for one city, stops on first failure
tests/check_<step>.py
```

## Config values to fix before coding

The agent must not guess any of these.

| Item | Value |
| :-- | :-- |
| Landsat LST | C2 L2 `ST_B10`, `DN * 0.00341802 + 149.0` = Kelvin |
| Landsat NDVI | Surface reflectance `SR_B5`, `SR_B4`, scale `0.0000275`, offset `-0.2` |
| Cloud mask | `QA_PIXEL` cloud, cloud shadow and dilated cloud bits |
| Landsat 9 | Starts late 2021, so the 2019 composite is Landsat 8 only. Do not "fix" this. |
| SMOD, BUILT-S epoch | 2020 for all three years |
| Season | 1 March inclusive to 1 June exclusive |
| Water mask | JRC Global Surface Water occurrence above 50 percent |
| City centres | Latitude and longitude per city, set once in `config.py` |
| Data access | No Drive exports. The grid is about 334 x 334 cells, so one request per image normally fits; tile only if a request is refused. Pull with `ee.data.computePixels` or `sampleRectangle`, write Parquet. Cap request size and retry on timeouts. |

## Prerequisite knowledge: the datasets

The agent should treat this section as ground truth and check each item against the Earth Engine catalogue page for that dataset before coding. If the catalogue disagrees, stop and report rather than choosing silently.

| Dataset | Facts the agent needs |
| :-- | :-- |
| GHSL SMOD (`JRC/GHSL/P2023A/GHS_SMOD_V2-0`) | An ImageCollection with one image per 5-year epoch. Band `smod_code`. Native resolution is 1 km in the Mollweide projection. Codes: 10 water, 11 very low density rural, 12 low density rural, 13 rural cluster, 21 suburban, 22 semi-dense urban cluster, 23 dense urban cluster, 30 urban centre. Observed epochs end at 2020; later epochs are projections. Classes are categorical, so sample them with nearest neighbour and never average the codes. About 11 cells of 300 m fall inside one 1 km class pixel. |
| GHS-BUILT-S (`JRC/GHSL/P2023A/GHS_BUILT_S`) | An ImageCollection, one image per epoch. Band `built_surface` is built-up area in square metres per 100 m pixel, so the maximum is 10,000. Built fraction is `built_surface / 10000`. Aggregate to 300 m by taking the mean of the nine 100 m pixels. Use the 2020 epoch. |
| Landsat 8 and 9 Collection 2 Level 2 (`LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`) | Optical bands are 30 m. The thermal band is acquired at 100 m and resampled to 30 m. Daytime overpass is about 10:30 local time, so LST is a mid-morning value, not the afternoon peak. Each satellite revisits every 16 days. Landsat 9 data begin in late 2021. Apply scale factors before any arithmetic, and mask clouds with `QA_PIXEL`. |
| JRC Global Surface Water (`JRC/GSW1_4/GlobalSurfaceWater`) | Band `occurrence` is percent of observations with water. Cells above the threshold in `config.py` are dropped. This matters most for Chennai and Kolkata, where the 50 km circle includes sea, rivers and wetlands. |

## Prerequisite knowledge: coordinates and grid

- **Projection:** EPSG:7755 is India NSF LCC with metre units. Define the grid in this CRS and sample all rasters at cell centres. If Earth Engine rejects the code, stop and report. Do not swap in another projection.
- **Grid size:** A 100 km box at 300 m is 334 x 334 cells (111,556). Keep only cells whose centre lies within 50 km of the city centre, which leaves about 87,000.
- **`grid_id`:** Build it deterministically from the cell's column and row index, for example `f"{col}_{row}"`, so the same cell has the same id in every year and every file.
- **Resampling:** Aggregate continuous rasters (LST, NDVI, built fraction) with a mean over the cells they cover. Sample categorical rasters (SMOD) by nearest neighbour. Never reproject a categorical raster with bilinear interpolation.
- **City centres for `config.py`:**

| City | Latitude | Longitude |
| :-- | :-- | :-- |
| Delhi | 28.6139 | 77.2090 |
| Kolkata | 22.5726 | 88.3639 |
| Chennai | 13.0827 | 80.2707 |
| Bengaluru | 12.9716 | 77.5946 |
| Hyderabad | 17.3850 | 78.4867 |

## Prerequisite knowledge: processing rules

- **Scale factors first:** LST in Kelvin is `ST_B10 * 0.00341802 + 149.0`. Reflectance is `SR_B* * 0.0000275 - 0.2`. NDVI is `(SR_B5 - SR_B4) / (SR_B5 + SR_B4)` on Landsat 8 and 9.
- **Cloud mask:** Drop pixels with the dilated cloud, cirrus, cloud, cloud shadow or snow bits set in `QA_PIXEL`. Also drop pixels with a large `ST_QA` uncertainty (scale 0.01 K; use the limit in `config.py`).
- **Composite:** Take the per-pixel median of all clear observations from 1 March to 31 May. Record the number of clear observations per cell in `n_obs`, and flag cells with fewer than the minimum set in `config.py`.
- **Rural reference:** For each city and year, `lst_rel = lst_k - median(lst_k of cells with ladder class rural)`, where rural means SMOD 11, 12 or 13 and water is excluded. Compute the median only after masking.
- **Expect surprises:** By day, bare dry rural land can be hotter than built-up land, so negative `lst_rel` in urban classes is a valid result, not a bug. Report it as found.
- **Same sensor caveat:** LST and NDVI come from the same Landsat scenes and share atmosphere and cloud effects. Built fraction and NDVI are also negatively correlated. Interpret the interaction term cautiously.

## Prerequisite knowledge: statistics

- **Spatial blocks:** Assign every cell to a 5 km block with `block_id = (floor(x / 5000), floor(y / 5000))`, using projected metres. All years of a cell stay in the same block.
- **Bootstrap (step 04):** Resample blocks with replacement, recompute the class median in each draw, repeat 1,000 times, and take the 2.5th and 97.5th percentiles. Never resample individual cells, because neighbouring cells are strongly autocorrelated and the intervals would be far too narrow.
- **GAM (step 05):** Use `pygam.LinearGAM(s(0) + s(1) + te(0, 1) + f(2))` with columns `built`, `ndvi` and `year`. The three years are pooled and `year` enters as a factor. Choose smoothing with `gridsearch`. Tensor terms are slow on tens of thousands of rows, so fit on a random subsample of cells (all years of each sampled cell) if a fit takes more than a few minutes, and record the subsample size.
- **Cross-validation:** Use scikit-learn `GroupKFold` with 5 folds and `block_id` as the group. Report the mean and spread of held-out R². Ordinary random folds are not allowed, because they leak information between neighbouring cells.
- **Plots:** Fig 2 is the built-up partial effect with a 95 percent band. Fig 3 is a heatmap of the `te(built, ndvi)` surface. Mask regions of the heatmap where there are almost no cells, since the model is extrapolating there.
- **Wording:** Use "is associated with", never "causes". A flat or non-monotonic curve is a valid result.

## Common failure modes

| Symptom | Likely cause | Action |
| :-- | :-- | :-- |
| Class counts look wrong or codes are fractional | SMOD was averaged or resampled bilinearly | Re-sample by nearest neighbour |
| `built` values above 1 | Forgot to divide by 10,000 | Fix the divisor and re-run step 01 |
| LST outside 270 to 340 K | Scale factor or offset missing | Re-apply both factors |
| Very few rural cells in Chennai or Kolkata | Sea and wetlands removed by the water mask, or the circle is mostly urban | Report the count and stop at the 200-cell check; do not lower the threshold |
| Earth Engine timeout or memory error | Request too large | Split into tiles of 100 x 100 cells and retry |
| GAM does not converge | Collinear terms or too few cells in a block | Report it in `summary.md`; do not change the model |

## Step contracts

Every step states its inputs, outputs and acceptance checks. If a check fails, the agent fixes and re-runs up to 3 times, then stops and reports. It never patches around a failure.

| Step | Inputs | Outputs | Acceptance checks |
| :-- | :-- | :-- | :-- |
| 00 Smoke test | EE project, credentials | Printed `OK` | EE initialises; one SMOD value and one Landsat value read. Everything else is blocked until this passes. |
| 01 Grid | City centre, SMOD 2020, BUILT-S 2020, JRC water | `grid.parquet` with `grid_id`, `x`, `y`, `smod`, `ladder_class`, `built`, `water` | About 87,000 cells (50 km radius at 300 m); `grid_id` unique; every class in {11-13, 21, 22, 23, 30} or flagged water; `built` in 0 to 1 |
| 02 Landsat | `grid.parquet`, Landsat 8/9 L2 | `landsat.parquet` with `grid_id`, `year`, `lst_k`, `ndvi`, `n_obs` | LST between 270 and 340 K; share of missing LST under a set limit per year; every year present |
| 03 Panel | Both parquet files | `panel.parquet` with `lst_rel` and `ladder_class` | At least 200 rural cells per year, else stop and flag; median `lst_rel` of rural cells is 0; water cells removed |
| 04 Gradient | `panel.parquet` | `gradient.csv`, Fig 1 | Median and 95 percent interval per class from 5 km spatial-block bootstrap; all five classes present |
| 05 GAM | `panel.parquet` | `cv.json`, Fig 2, Fig 3 | `lst_rel ~ s(built) + s(ndvi) + te(built, ndvi)`; 5 km spatial-block CV R² reported; fit converges |
| 06 Summary | All outputs | `summary.md` | Contains median `lst_rel` per class, CV R², curve shape, caveats, and the three sentences (done, shows, could be wrong) |

## Setup the agent cannot do

These are human prerequisites.

1. Create or choose a Google Cloud project with the Earth Engine API enabled.
2. Run `earthengine authenticate` once, or supply a service account key.
3. Set `EE_PROJECT` in the environment.

## Execution protocol

1. Run `00_smoke_test.py`. Continue only if it prints `OK`.
2. Build and run steps 01 to 06 for **Hyderabad only**, one step at a time, running each step's check before the next.
3. After step 06, stop and show the six outputs (class map, LST map, cell-count table, Figs 1 to 3, summary). Do not start another city until told.
4. For the other four cities, run `run_city.sh <city>` unchanged. Do not edit any script. Flag anything odd in that city's `summary.md`.
5. Finally, paste the five `summary.md` files into one comparison table.

## Prompt to paste to the agent

```text
You are implementing the plan in this document. Build the scripts and tests
in the repo layout exactly as listed. Use only the datasets, years, metrics
and model named here. Do not add datasets, metrics, models, years, checks,
files or refactors. Ask first if something seems missing.

Work one step at a time. After each step run its check script. If a check
fails, fix and re-run, up to 3 attempts, then stop and report the failure.
Do not work around a failed check.

Run Hyderabad only. When step 06 finishes, stop and show me the outputs.
Do not run any other city until I say so. Never edit scripts per city; if a
city needs special handling, note it in summary.md.

With every result give three sentences: what was done, what it shows, what
could be wrong. Report null and contradictory results plainly. Results are
associations, not causal effects.
```
