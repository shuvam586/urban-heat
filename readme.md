# Nonlinear Urbanization - Heat Relationships Across Indian Cities

## 1. Proposed title

A GeoML Framework for Identifying Nonlinear Urbanization–Heat Relationships and Vegetation-Mediated Cooling Across Indian Cities (2015–2025)

## 2. Final research question

How does the relationship between urban built-up intensity and land surface temperature vary across Indian cities, and to what extent does vegetation modify this relationship through nonlinear effects and potential thresholds?

We will investigate four cities initially: Delhi, Hyderabad, Bengaluru, Chennai and Kolkata. These provide contrasting urban and climatic settings for testing whether the identified relationships generalize across different environments.

## 3. What problem are we trying to solve?

Urban expansion replaces vegetation and permeable surfaces with buildings, roads and other impervious materials. These changes are associated with higher land surface temperatures, but the relationship may not be linear.

Three important questions remain for our study:

- Nonlinear effects: Does LST increase gradually with built-up intensity, or are there ranges beyond which the increase becomes substantially steeper?
- Vegetation moderation: Does vegetation weaken the relationship between built-up intensity and LST, and does this effect depend on how densely built-up an area already is?
- Geographic variation: Do these relationships and potential thresholds differ across cities, climates and years?

A simple correlation cannot adequately answer these questions. We need a model that captures nonlinear relationships, interactions and spatial variation, followed by validation to establish whether the patterns are robust.

Our goal is to identify where urbanization is most strongly associated with surface heating, where vegetation is associated with the greatest cooling benefit, and whether these patterns are consistent across cities and time.

## 4. How we will proceed

Phase 1 - Data collection

2015–2025

Collect Landsat 8/9 surface temperature and reflectance data through Google Earth Engine. Derive LST, NDBI and NDVI for consistent hot-season periods. Collect climate covariates where appropriate.

Phase 2 - Spatial-temporal dataset

Aggregate the variables into consistent 300 m grid cells across each urban and peri-urban study area. Produce comparable annual or seasonal observations, with cloud masks, valid-observation counts and quality checks.

Phase 3 - Nonlinear modeling

Compare linear regression with Generalized Additive Models (GAMs). Model NDBI and NDVI jointly, including their interaction, to investigate nonlinear relationships and vegetation moderation.

Phase 4 - Threshold identification

Estimate candidate built-up intensity thresholds using explicit change-point analysis. Quantify uncertainty and test whether candidate thresholds persist across years and geographic subsets. Use SHAP or ALE as complementary interpretation methods.

Phase 5 - Cross-city comparison

Compare relationships and threshold estimates across Delhi, Hyderabad, Bengaluru and Jaipur. Use spatially separated validation and year-based tests to assess generalization and temporal stability.

Phase 6 - Research findings

Produce threshold estimates with uncertainty intervals, interaction plots, city-level comparison maps and an assessment of where vegetation is most strongly associated with reduced LST.

## 5. Variables and methods

| Component          | Definition                                                             |
| ------------------ | ---------------------------------------------------------------------- |
| Dependent variable | Seasonal mean LST in °C                                                |
| Main predictor     | NDBI, representing built-up intensity                                  |
| Moderator          | NDVI, representing vegetation density                                  |
| Controls           | Year, seasonal timing, elevation and selected meteorological variables |
| Main method        | GAM with nonlinear NDBI–NDVI interaction                               |
| Supporting methods | Linear baseline, change-point analysis, SHAP/ALE                       |
| Validation         | Spatial-block and temporal validation                                  |

NDBI is a proxy for built-up intensity, not a direct measurement of building density. We should acknowledge its limitations and, if feasible, validate it against an independent built-up land-cover dataset.

Heatwave days will remain a secondary analysis, using daily near-surface air temperature and a defined meteorological heatwave criterion rather than treating high satellite LST as a heatwave.

## 6. What is the expected research contribution?

The paper will aim to contribute three things:

1. Nonlinear characterization: Determine whether the built-up intensity–LST relationship has identifiable thresholds rather than assuming a linear effect.
2. Vegetation interaction analysis: Quantify how the association between built-up intensity and LST changes at different vegetation levels.
3. Cross-city generalization: Establish whether the identified relationships and thresholds are geographically and temporally robust.

These are intended contributions, not established findings. Novelty must be verified through a focused literature review, and any threshold must be demonstrated empirically rather than assumed in advance.

The study will establish associations, not prove that urbanization or vegetation independently causes temperature changes. Strong causal claims would require a more specific identification strategy.