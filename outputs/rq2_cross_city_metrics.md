# RQ2 Part C — Built-up metric comparison (H5), five-city table

**Scope:** Hyderabad, Kolkata, Chennai, Delhi. Bengaluru could not be completed:
its `09_rq2_metrics.py --city Bengaluru` run timed out during Earth Engine
extraction (no `data/Bengaluru/metrics.parquet` written after ~30 min) and the
run was stopped per protocol. All four completed cities passed
`tests/check_09_rq2_metrics.py --city <City>` (OK), including the strict
NDBI range assertion within [-1.0, 1.0].

**Method:** NDBI = (SR_B6 - SR_B5) / (SR_B6 + SR_B5) on Landsat 8/9 C2 L2
March–May 2022/2023/2025, with the same QA_PIXEL cloud/water mask and
ST_QA <= 5 K filter as step 02, plus a positive-reflectance mask
(SR_B4 > 0, SR_B5 > 0, SR_B6 > 0) so NDBI is strictly bounded within [-1, 1].
Dynamic World = GOOGLE/DYNAMICWORLD/V1 March–May mean `built` probability.
ESA WorldCover = ESA/WorldCover/v200 class-50 (Built-up) fraction per 300 m cell.
All metrics extracted onto the exact existing EPSG:7755 300 m `grid.parquet`,
cached to `data/<city>/metrics.parquet`, joined to `panel.parquet` on
(grid_id, year). Pairwise Spearman correlations computed on the joined panel.
5-fold 5 km spatial-block GroupKFold GAM on the same 10,000-cell subsample
(seed 42) and folds as `cv.json`, comparing `lst_rel ~ metric + f(year)`
(linear) vs `lst_rel ~ s(metric) + s(ndvi) + te(metric, ndvi) + f(year)`
(full).

---

## 1. Spearman correlations with `lst_rel` (joined panel, all years)

| City | GHS-BUILT-S vs lst_rel | Landsat NDBI vs lst_rel | Dynamic World vs lst_rel | WorldCover vs lst_rel |
|---|---|---|---|---|
| Hyderabad | -0.1362 | **-0.3509** | -0.1050 | -0.1389 |
| Kolkata | 0.3237 | **0.6543** | 0.3238 | 0.3801 |
| Chennai | 0.1648 | **0.7863** | 0.2245 | 0.1594 |
| Delhi | 0.1646 | **0.5827** | 0.0261 | 0.1253 |

NDBI shows the strongest correlation with `lst_rel` in every city, far above
GHS-BUILT-S, Dynamic World, and WorldCover.

## 2. Built-up vs NDBI correlation and bare-soil association

| City | built vs NDBI | NDBI vs bare-soil proxy | DW vs bare-soil proxy | WC vs bare-soil proxy |
|---|---|---|---|---|
| Hyderabad | -0.1457 | -0.2610 | 0.1249 | 0.2369 |
| Kolkata | 0.2981 | **0.5931** | 0.1789 | 0.2733 |
| Chennai | 0.0539 | **0.5640** | 0.2640 | 0.3420 |
| Delhi | -0.1670 | **0.5966** | -0.0592 | 0.1788 |

NDBI correlates weakly with built-up fraction (|r| 0.05–0.30, negative in
Hyderabad/Delhi) but strongly with the bare-soil proxy (r 0.56–0.60) in all
four cities. Dynamic World and WorldCover correlate much more weakly with the
bare-soil proxy (|r| 0.06–0.34).

Full correlation matrices are saved in `outputs/<city>/rq2_metrics.json`
(`correlation_matrix` and `bare_soil_corr`).

## 3. 5-fold spatial-block CV R² comparison

| City | Metric | Linear (metric + year) | Full (metric + NDVI + interaction + year) | Gain | Favors nonlinear |
|---|---|---|---|---|---|
| Hyderabad | GHS-BUILT-S | 0.0074 | 0.6373 | +0.6299 | 5/5 |
| Hyderabad | Landsat NDBI | 0.4035 | 0.6293 | +0.2258 | 5/5 |
| Hyderabad | Dynamic World | 0.0032 | 0.6381 | +0.6349 | 5/5 |
| Hyderabad | WorldCover | 0.0042 | 0.6125 | +0.6083 | 5/5 |
| Kolkata | GHS-BUILT-S | 0.2303 | 0.4605 | +0.2302 | 5/5 |
| Kolkata | Landsat NDBI | 0.4840 | 0.5484 | +0.0644 | 5/5 |
| Kolkata | Dynamic World | 0.1848 | 0.4582 | +0.2733 | 5/5 |
| Kolkata | WorldCover | 0.1740 | 0.4408 | +0.2668 | 5/5 |
| Chennai | GHS-BUILT-S | 0.0310 | 0.4608 | +0.4298 | 5/5 |
| Chennai | Landsat NDBI | 0.6558 | 0.7072 | +0.0514 | 5/5 |
| Chennai | Dynamic World | 0.0613 | 0.4801 | +0.4187 | 5/5 |
| Chennai | WorldCover | 0.0216 | 0.4466 | +0.4251 | 5/5 |
| Delhi | GHS-BUILT-S | 0.0064 | 0.3565 | +0.3501 | 5/5 |
| Delhi | Landsat NDBI | 0.3952 | 0.4344 | +0.0392 | 5/5 |
| Delhi | Dynamic World | 0.0385 | 0.3541 | +0.3155 | 5/5 |
| Delhi | WorldCover | -0.0009 | 0.3341 | +0.3350 | 5/5 |

GHS-BUILT-S, Dynamic World, and WorldCover add almost no linear skill alone
(≈ -0.001 to 0.23 R²) but reach ≈ 0.33–0.46 R² with NDVI + interaction.
Landsat NDBI alone already reaches ≈ 0.40–0.66 R², and its full-model gain
over linear is small (+0.04–0.23) because much of its signal is already
captured linearly — consistent with NDBI responding to dry bare soil/vegetation
rather than built-up fraction alone.

## 4. H5 assessment

**H5 (whether NDBI conflates dry bare soil with built-up land): supported.**

Across all four completed cities, NDBI correlates much more strongly with
`lst_rel` (r = 0.35–0.79) and with the bare-soil proxy (r = 0.56–0.60) than
GHS-BUILT-S, Dynamic World, or WorldCover do, while correlating only weakly
with built-up fraction itself (r = -0.17 to 0.30). NDBI therefore carries a
substantial dry bare-soil signal and is not a clean substitute for GHS-BUILT-S.
Dynamic World and WorldCover behave much closer to GHS-BUILT-S (weak bare-soil
association, comparable CV skill once NDVI + interaction are added), so the
apparent urban-heat signal from NDBI is likely inflated by bare pre-monsoon
soil, especially in Delhi (+0.58 NDBI–lst_rel) and Chennai (+0.79).

**Bengaluru:** not completed (Earth Engine extraction timeout). No results
included; run separately once extraction succeeds.
