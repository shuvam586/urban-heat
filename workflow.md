# Workflow: Remaining Phases

Completed: Phase 1 — Literature review and research-gap identification; Phase 2.1 — Finalized the five study cities: Delhi, Kolkata, Chennai, Bengaluru and Hyderabad.

The remaining work begins at Phase 2.2: defining urban boundaries. The following plan covers the rest of the project in execution order.

## Phase 2 — Study-area selection and spatial design

### 2.2 Define urban boundaries

Objective: Establish comparable geographic study areas for all five cities.

Tasks:

- Obtain consistent urban boundaries from official metropolitan sources or a reliable built-up-area dataset.
- Define the urban core and surrounding peri-urban region for each city.
- Decide whether boundaries will remain fixed throughout 2015–2025.
- Document the source, date and method used to define each boundary.
- Check whether the selected regions contain sufficient variation in built-up intensity and vegetation.

Deliverable: Five validated study-area boundaries.

### 2.3 Establish the spatial grid

Objective: Create consistent spatial units for the analysis.

Tasks:

- Begin with a 300 m × 300 m grid.
- Use an appropriate projected coordinate system for grid construction.
- Assign each grid cell a unique identifier and city identifier.
- Define how partially covered cells at the study-area boundaries will be handled.
- Retain the geometry or centroid coordinates for mapping and spatial validation.

The 300 m grid is an initial analysis resolution, not the native thermal resolution of Landsat. We will test an alternative resolution during robustness analysis.

Deliverable: A spatial grid dataset covering all five study areas.

### 2.4 Finalize temporal sampling

Objective: Establish comparable observations across the 2015–2025 period.

Tasks:

- Decide on the primary seasonal window for each year's analysis.
- Initially evaluate March–June, but inspect cloud cover, seasonal differences and data availability across cities.
- Define minimum valid satellite-observation requirements.
- Decide how missing observations and years with inadequate coverage will be handled.
- Specify whether the primary dataset will use annual seasonal composites or monthly observations.

Deliverable: A documented spatial-temporal sampling protocol.

Phase 2 completion criterion: All five cities have validated boundaries, a consistent grid and a finalized sampling protocol.

## Phase 3 — Geospatial data collection and preprocessing

Objective: Build the Google Earth Engine pipeline to derive LST, NDBI and NDVI consistently for all cities and years.

### 3.1 Collect satellite data

Use Landsat Collection 2 Level-2 products for 2015–2025.

| Variable   | Source and derivation                                    |
| ---------- | -------------------------------------------------------- |
| LST        | Landsat surface-temperature product                      |
| NDVI       | Near-infrared and red surface reflectance                |
| NDBI       | Shortwave-infrared and near-infrared surface reflectance |
| Water mask | Optional MNDWI or a validated water dataset              |
| Elevation  | Optional digital elevation model                         |

Use Landsat 8 throughout its available study period and Landsat 9 from its operational period onward. Record the sensor contributing to each composite.

### 3.2 Preprocess imagery

Implement the following steps:

1. Filter images by study area and date.
2. Apply cloud, cloud-shadow and saturation masks.
3. Apply the documented scale factors and offsets to surface reflectance and surface temperature.
4. Calculate NDVI and NDBI from the appropriate reflectance bands.
5. Convert LST to degrees Celsius.
6. Apply consistent rules for water and invalid temperature observations.
7. Generate seasonal composites.
8. Aggregate the variables to the spatial grid.
9. Record observation counts and quality indicators.

### 3.3 Validate the extraction pipeline

Before processing the entire dataset:

- Inspect sample images from each city.
- Check that LST values and index distributions are plausible.
- Verify that masking and scaling are applied correctly.
- Compare selected locations against the original Landsat layers.
- Check whether any city or year has unusually poor data coverage.

Deliverable: Reproducible Earth Engine scripts and quality-controlled seasonal raster products.

Phase 3 completion criterion: The extraction process produces consistent, validated outputs across the five cities.

## Phase 4 — Dataset construction and exploratory analysis

Objective: Produce the analysis-ready dataset and verify that it can support nonlinear modeling.

### 4.1 Construct the dataset

Create one row per grid cell per year for the primary seasonal analysis.

| Field                     | Description                  |
| ------------------------- | ---------------------------- |
| `grid_id`                 | Unique grid-cell identifier  |
| `city`                    | Study city                   |
| `year`                    | Observation year             |
| `lst_c`                   | Seasonal mean LST in °C      |
| `ndbi`                    | Seasonal NDBI                |
| `ndvi`                    | Seasonal NDVI                |
| `n_obs`                   | Number of valid observations |
| `geometry` or coordinates | Spatial location             |

Retain additional quality indicators and any selected control variables.

### 4.2 Perform exploratory analysis

Tasks:

- Calculate descriptive statistics for all variables.
- Examine missing values, outliers and data coverage.
- Plot LST against NDBI and NDVI.
- Produce maps for representative years.
- Calculate Pearson and Spearman correlations as descriptive baselines.
- Examine temporal trends and differences between cities.
- Check for extreme or poorly represented NDBI and NDVI values.

### 4.3 Assess data suitability

Before modeling, verify that:

- Each city contains enough variation in NDBI.
- NDVI has sufficient variation to test vegetation moderation.
- Missing data do not disproportionately exclude particular land-cover types.
- Repeated observations and spatial dependence are accounted for in later analyses.

Deliverable: A versioned CSV or Parquet dataset, data dictionary, exploratory plots and quality report.

Phase 4 completion criterion: The dataset is sufficiently complete and representative for the planned model comparisons.

## Phase 5 — Baseline and nonlinear modeling

Objective: Determine whether nonlinear models capture relationships that a linear model misses.

### 5.1 Establish the linear baseline

Fit a regression model:

\\[ LST=\beta_0+\beta_1NDBI+\beta_2NDVI+\epsilon \\]

This establishes the basic associations between built-up intensity, vegetation and surface temperature.

### 5.2 Fit a Generalized Additive Model

Allow nonlinear relationships:

\\[ LST=\beta_0+s_1(NDBI)+s_2(NDVI)+\epsilon \\]

Compare the model with the linear baseline using held-out data.

### 5.3 Test vegetation moderation

Fit a model that allows the NDBI–LST relationship to vary with NDVI:

\\[ LST=\beta_0+s(NDBI,NDVI)+\epsilon \\]

Evaluate whether the interaction improves model performance and whether the estimated response surface is supported by sufficient observations.

### 5.4 Use complementary machine learning

Fit XGBoost as a secondary model. Use SHAP or accumulated local effects (ALE) to investigate feature effects and interactions.

These methods complement the GAM; they should not be treated as independent proof of a threshold.

### 5.5 Compare models

Evaluate:

- RMSE and MAE on held-out observations.
- \\(R^2\\) as a measure of predictive fit.
- Residual patterns and spatial autocorrelation.
- Model complexity and uncertainty.
- Performance under spatially separated and temporally separated validation.

Deliverable: Model comparison, diagnostics and interpretable nonlinear response curves.

Phase 5 completion criterion: Evidence establishes whether the nonlinear model adds value over the linear baseline.

## Phase 6 — Threshold identification and robustness testing

Objective: Estimate candidate built-up intensity thresholds and determine whether they are statistically supported.

### 6.1 Define candidate thresholds

Use explicit change-point or segmented-regression methods to estimate where the NDBI–LST relationship changes slope.

A nonlinear curve does not necessarily contain a single threshold, so the analysis must allow for the possibility that no clear breakpoint exists.

### 6.2 Quantify vegetation moderation

Estimate the NDBI–LST relationship at different observed NDVI levels.

Test whether:

- The candidate breakpoint varies with NDVI.
- The slope beyond a breakpoint changes with NDVI.
- A smooth interaction describes the data better than a single change point.

### 6.3 Quantify uncertainty

Use appropriate uncertainty estimation, accounting for spatial dependence where possible.

Report the estimated threshold, its uncertainty interval, sensitivity to model assumptions and the amount of data supporting the estimate.

### 6.4 Test stability

Repeat the analysis across:

- Different years.
- Spatially separate regions.
- Alternative model specifications.
- Alternative grid resolutions and seasonal definitions.

Deliverable: Threshold estimates, uncertainty intervals and stability analyses.

Phase 6 completion criterion: Each reported threshold is supported by explicit statistical evidence and its limitations are documented.

## Phase 7 — Cross-city comparison and robustness

Objective: Determine whether the relationships generalize across the five cities.

### 7.1 Fit city-specific and pooled models

Compare independently fitted city models against a pooled model that accounts for city and time differences.

### 7.2 Conduct cross-city validation

Use a leave-one-city-out design:

- Train on four cities.
- Evaluate on the fifth.
- Repeat for each city.

This tests geographic transfer rather than merely predicting held-out pixels from the same locations.

### 7.3 Compare findings

For each city, compare:

- Nonlinear response curves.
- Candidate thresholds and their uncertainty.
- Vegetation interaction patterns.
- Out-of-sample predictive errors.
- Temporal and spatial stability.

### 7.4 Optional secondary analysis: heatwave days

If the primary LST analysis is successful, investigate meteorological heatwaves using daily air-temperature data, such as ERA5-Land, and a clearly defined heatwave criterion.

Keep this separate from satellite LST analysis: surface heating and air-temperature heatwaves are different outcomes.

Deliverable: Cross-city comparison tables, validation results and robustness analyses.

Phase 7 completion criterion: The study distinguishes relationships that generalize from those that are city-specific.

## Phase 8 — Paper writing and reproducibility

Objective: Convert the validated analysis into a research manuscript.

Tasks:

- Write the introduction around the verified research gap.
- Document the study areas, data sources and preprocessing methods.
- Describe model specifications and validation procedures precisely.
- Present nonlinear response curves, threshold estimates and uncertainty.
- Discuss cross-city differences and alternative explanations.
- State limitations and avoid causal claims unsupported by the design.
- Prepare maps, tables, supplementary material and reproducible code.

Deliverable: Complete manuscript, figures, tables and documented analysis pipeline.

## Execution milestones

| Milestone | Required result                                |
| --------- | ---------------------------------------------- |
| M1        | Boundaries and grid finalized                  |
| M2        | Earth Engine pipeline validated                |
| M3        | Analysis-ready dataset completed               |
| M4        | Linear and nonlinear models compared           |
| M5        | Thresholds estimated and tested                |
| M6        | Cross-city validation completed                |
| M7        | Manuscript and reproducible materials prepared |

Immediate next task: Phase 2.2 — define the five urban study boundaries. This should be completed before extracting satellite data, because boundary choices affect every subsequent spatial calculation.