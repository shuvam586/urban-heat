# Urbanisation and Surface Heat in Five Indian Cities

**A GHSL-anchored study of urban–rural temperature gradients, built-up response and settlement history (2015–2025)**

Cities are hotter than the land around them, but the size and shape of that difference is not a simple function of how much is built. This project studies land surface temperature (LST) in Delhi, Kolkata, Chennai, Bengaluru and Hyderabad using a harmonised settlement classification, a continuous built-up surface record, and annual Landsat composites.

The design replaces concentric "core" and "peri-urban" rings with the GHSL Degree of Urbanisation ladder. Every 300 m cell is placed on a rural-to-urban-centre scale using the same rule in every city. That makes the urban–rural comparison reproducible, lets the rural reference be tested rather than assumed, and opens a question a one-year snapshot cannot answer: does the way a place urbanised leave a measurable thermal signature?

The study is observational. Results are spatial and temporal associations, not causal effects.

---

## 1. Research questions

| ID | Question | Main evidence |
| :-- | :-- | :-- |
| **RQ1 — Gradient** | How does LST change along the GHSL rural-to-urban-centre ladder in each city, and how sensitive is the urban–rural contrast to how the rural reference is defined? | Class-wise contrasts with spatial-block bootstrap intervals under three reference definitions |
| **RQ2 — Response and context** | How nonlinear is the LST response to built-up intensity, does vegetation moderate it, does it depend on urban context, and how much does the choice of built-up metric matter? | GAM partial effects; built-up × vegetation interaction; by-class smooths; metric comparison |
| **RQ3 — Trajectory** | Does when and how fast a cell became built-up explain present-day LST beyond current built-up intensity? | Nested models with GHSL history; matched comparisons at fixed built fraction |

### Hypotheses

| ID | Hypothesis |
| :-- | :-- |
| H1 | LST relative to the rural reference rises along the ladder, but the magnitude depends on the reference definition and may be small or negative by day where rural land is bare. |
| H2 | The built-up–LST relationship is nonlinear, with possible thresholds. |
| H3 | Vegetation moderates the built-up–LST relationship. |
| H4 | The shape and magnitude of relationships differ across cities. |
| H5 | NDBI partly captures bare-soil and dryness effects, distorting estimated relationships. |
| H6 | The built-up–LST response differs by urban context at the same built fraction. |
| H7 | Built-up age or trajectory adds explanatory information after current built-up fraction. |

Hypotheses are tested, not assumed. Null and contradictory results are reported.

---

## 2. Why anchor the study on GHSL

- **A ring is not an urban–rural axis.** The edge of an Indian megacity is usually suburban, semi-dense or dense-rural settlement. A "peri-urban" buffer is not a rural reference.
- **Anomalies depend on the window.** Subtracting a city-year mean makes the baseline move with the urban/rural mix of the study area, so cities are not comparable.
- **NDBI is a weak built-up anchor.** It responds to bare soil and surface dryness, which is acute in pre-monsoon India. An independent built-up surface record is needed.
- **History matters.** GHSL classifies settlement from 1975 onward and provides built-up surface back to 1975. That turns "how hot is built-up land?" into "does urbanisation history still show up in today's heat?"

---

## 3. Design at a glance

| Element | Plan |
| :-- | :-- |
| Cities | Delhi, Kolkata, Chennai, Bengaluru, Hyderabad |
| Spatial frame | Fixed 50 km radius around each city centre; no core/buffer polygons. Urbanness is a per-cell attribute. |
| Unit of analysis | 300 m cell × year (annual March–May composite) |
| Projection / grid | EPSG:7755 (India NSF LCC), 300 m cells, deterministic `grid_id` |
| Urban–rural ladder | GHSL SMOD: rural (11–13), suburban (21), semi-dense (22), dense (23), urban centre (30); water (10) and no-data (−200) excluded |
| Primary outcome | `lst_rel_rural`: cell LST minus the median LST of that city-year's rural reference |
| Primary built-up measure | `ghsl_built`: GHS-BUILT-S built fraction, 100 m aggregated to 300 m |
| Built-up comparisons | Dynamic World `p_built` / `f_built`, WorldCover built fraction, NDBI |
| Time | Landsat 2015–2025; GHSL observed epochs 1990–2020; Dynamic World 2016–2025 |
| Models | GAMs (`pygam`), `statsmodels` checks, spatial-block cross-validation, leave-one-year-out, leave-one-city-out |
| Optional extension | Landsat 5/7 LST for 2000, 2005, 2010 (gated; only if the history effect is stable) |

Primary season is March–May (1 March inclusive to 1 June exclusive). March–June is the robustness season.

---

## 4. Data

| Dataset | Earth Engine collection | Role |
| :-- | :-- | :-- |
| GHSL SMOD P2023A | `JRC/GHSL/P2023A/GHS_SMOD_V2-0` | Per-cell urban–rural class; ladder; trajectory |
| GHS-BUILT-S P2023A | `JRC/GHSL/P2023A/GHS_BUILT_S` | Continuous built-up surface and history |
| GHS-POP P2023A | `JRC/GHSL/P2023A/GHS_POP` | Population context |
| GHS-BUILT-H P2023A | `JRC/GHSL/P2023A/GHS_BUILT_H` | Building height |
| Landsat 8/9 C2 L2 | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | LST, NDVI, NDBI, BSI, MNDWI, albedo |
| Dynamic World | `GOOGLE/DYNAMICWORLD/V1` | Nine-class land-cover probabilities and hard fractions |
| ESA WorldCover 2021 | `ESA/WorldCover/v200` | Independent land-cover fractions |
| SRTM | `USGS/SRTMGL1_003` | Elevation and slope |
| JRC Global Surface Water | `JRC/GSW1_4/GlobalSurfaceWater` | Water-occurrence screen |
| ERA5-Land | `ECMWF/ERA5_LAND/DAILY_AGGR` | Seasonal temperature and precipitation context |
| CHIRPS | `UCSB-CHG/CHIRPS/DAILY` | Seasonal and antecedent rainfall |
| MODIS Aqua | `MODIS/061/MYD11A2` | Night LST comparison |

Collection IDs, band names, scale factors and licences are confirmed against the Earth Engine catalogue and recorded in `docs/data_dictionary.md` before the first production export.

---

## 5. Pipeline

| Stage | What happens | Key output |
| :-- | :-- | :-- |
| **0. Feasibility** | Run raster-based ladder, reference and LST checks in Hyderabad, then Kolkata and Delhi. Compare built-measure agreement and trajectory sizes. Freeze definitions at Gate 0. | Five-city feasibility summaries and a frozen definitions sheet |
| **1. Spatial framework** | Production 300 m grid and GHSL attributes for all five cities. | `UH3_grid_<City>`, `UH3_attrs_<City>` |
| **2. Extraction** | Annual Landsat, Dynamic World, static and climate covariates. Hyderabad first, then scale. | Cell-year CSV batches |
| **3. Panel and QC** | Join on `grid_id` and `year`, apply QC in a fixed order, derive outcomes, run exploratory analysis. | Versioned Parquet panel, QC report, EDA figures |
| **4. RQ1** | LST relative to three rural-reference definitions along the ladder, with bootstrap uncertainty. | Gradient tables and figures |
| **5. RQ2** | Staged GAMs, vegetation interaction, context-dependent response, built-up metric comparison. | Model objects, partial effects, metric comparison |
| **6. RQ3** | Built-up age and trajectory, nested models, matched comparisons. | History effect estimates; Tier 2 decision |
| **7. Validation** | Spatial-block CV, leave-one-year-out, leave-one-city-out, robustness suite. | Validation tables and threshold evidence |
| **8. Manuscript** | Figures, tables, reproducibility package. | Manuscript and archive |

All Earth Engine work runs through the Python `earthengine-api` in Jupyter notebooks. Every map, distribution and diagnostic is plotted inline in the notebook that produces it, and saved to `reports/figures/`. There is no Code Editor script and no browser step.

**Do not begin production extraction before Gate 0.** The feasibility phase exists to stop a large, expensive pipeline from being built on an inadequate rural reference or an unworkable class structure.

---

## 6. Repository layout (planned)

```text
.
├── notebooks/                  # active GEE pipeline: Python API + inline plots
│   ├── config.py               # project, asset prefix, city list
│   ├── ee_helpers.py           # shared masks, indices, export helpers
│   ├── 00_feasibility.ipynb
│   ├── 01_window_and_grid.ipynb
│   ├── 02_ghsl_attributes.ipynb
│   ├── 03_qc_checks.ipynb
│   ├── 04_landsat_extraction.ipynb
│   ├── 05_dynamic_world_fractions.ipynb
│   ├── 06_static_covariates.ipynb
│   ├── 07_climate_covariates.ipynb
│   └── 08_landsat_legacy.ipynb
├── pipeline/                   # Python assembly, QC and EDA
│   ├── config.py
│   ├── assemble.py
│   ├── qc.py
│   ├── derive.py
│   └── eda.py
├── analysis/                   # Python GAM, threshold and validation modules
│   ├── 00_prepare.py
│   ├── 01_rq1_gradient.py
│   ├── 02_rq2_models.py
│   ├── 03_rq2_metrics.py
│   ├── 04_rq3_trajectory.py
│   ├── 05_thresholds.py
│   ├── 06_validation.py
│   └── 07_robustness.py
├── docs/
│   └── data_dictionary.md
├── runs/                       # one manifest per run: parameters, task IDs, commit
├── reports/                    # QC tables and inline figure exports
├── data/                       # panels and derived datasets (gitignored)
├── exports/                    # raw Earth Engine exports (gitignored)
├── legacy/                     # superseded scripts, kept for provenance only
├── readme.md
├── workflow.md
└── TODO.md
```

---

## 7. Getting started

1. Create the Python environment from `environment.yml` or `requirements.txt`, run `ee.Authenticate()` once, and initialize with `ee.Initialize(project=...)`.
2. Set `PROJECT` and `BASE` in `notebooks/config.py`.
3. Open `notebooks/00_feasibility.ipynb` and run it top to bottom for **Hyderabad only**.
4. Read the figures inline; they are also saved under `reports/figures/phase0/`. Record parameters and task IDs in `runs/`.
5. Review the feasibility results against the Gate 0 criteria in `workflow.md`.
6. Freeze the window radius, rural reference, history threshold and QC rules.
7. Build the production grid and GHSL attributes for Hyderabad.
8. Extract Landsat and Dynamic World for Hyderabad, assemble the panel, and validate the join and QC.
9. Only after the Hyderabad pilot passes Gate A, scale to Kolkata, Delhi, Chennai and Bengaluru.

The actionable checklist lives in `TODO.md`. The full design and decision rules live in `workflow.md`.

---

## 8. Status

| Stage | Status |
| :-- | :-- |
| Feasibility (Phase 0) | All five cities run; Gate 0 pending |
| Spatial framework and GHSL attributes | Not started |
| Environmental extraction | Not started |
| Panel assembly and QC | Not started |
| RQ1–RQ3 analyses | Pending |
| Validation and robustness | Pending |
| Manuscript | Pending |

No production data have been extracted for this design.

---

## 9. Scope and limitations

- The outcome is satellite **land surface temperature**, not near-surface air temperature. Heatwave claims are out of scope unless a separate air-temperature analysis is added.
- GHSL classes are 1 km; the analysis grid is 300 m. About eleven cells share a class. Class is treated as context, not as a precise per-cell measurement.
- GHS-BUILT-S and SMOD are related products. Stratifying by class and regressing on built fraction restricts the predictor range. Pooled and by-class results are reported together.
- GHSL observed epochs end in 2020. Later epochs are projections and are not used as data.
- Dynamic World begins in 2015; DW-based models are restricted to 2016 onward.
- Built-up age is confounded with location: older cells tend to sit nearer the city centre. The trajectory analysis is a space-for-time design and supports association, not causation.
- Thresholds are reported only where stable, away from the data edge, and supported by uncertainty analysis. A no-threshold result is a valid result.

---

## 10. Documentation

| File | Purpose |
| :-- | :-- |
| `workflow.md` | Full execution plan: phases, scripts, variable definitions, QC rules, models, gates and decision log |
| `TODO.md` | The live checklist; the single place where actionable tasks are tracked |
| `docs/data_dictionary.md` | Variable names, units, sources and derivations (created in Phase 1) |
