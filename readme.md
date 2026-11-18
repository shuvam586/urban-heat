# Urbanisation and Mid-Morning Land Surface Temperature Across Five Indian Cities: Complete Research Dossier

## 1. Study Motivation, Research Questions, and Hypotheses

Rapid urbanisation across India spans sharply contrasting hydro-climatic regimes—from humid coastal deltas to semi-arid inland plateaus. Standard urban heat studies often rely on arbitrary concentric distance rings around a city centre and use spectral indices such as the Normalised Difference Built-up Index (NDBI) as direct proxies for urban density. Both choices can distort daytime surface temperature comparisons in pre-monsoon Indian landscapes, where fallow agricultural soil surrounding cities is hot and dry, and bare soil shares high shortwave-infrared reflectance with impervious surfaces.

To evaluate how urbanisation shapes mid-morning land surface temperature (LST) across diverse Indian urban morphologies without those artefacts, this study anchors five major metropolitan regions—**Delhi, Kolkata, Chennai, Bengaluru, and Hyderabad**—on a uniform spatial grid and a standardised settlement-density ladder.

### Initial Research Questions

| ID | Research Question | Primary Empirical Evidence |
| :--- | :--- | :--- |
| **RQ1 — Gradient** | How does LST change along the GHSL rural-to-urban-centre ladder in each city, and how sensitive is the urban–rural contrast to how the rural reference is defined? | Class-wise relative LST contrasts with $5\text{ km}$ spatial-block bootstrap confidence intervals under three rural reference definitions. |
| **RQ2 — Response & Context** | How nonlinear is the LST response to built-up intensity, does vegetation moderate it, does it depend on urban context, and how much does the choice of built-up metric matter? | Generalised Additive Model (GAM) partial effects; built-up $\times$ vegetation interaction surfaces; within-context smooths; and cross-metric comparisons across four built-up datasets. |
| **RQ3 — Trajectory** *(Scoped Out)* | Does when and how fast a cell became built-up explain present-day LST beyond current built-up intensity? | *Deliberately excluded from the active scope to maintain a single-epoch baseline and avoid confounding multi-decade reconstruction errors.* |

### Initial Hypotheses Tested

| ID | Hypothesis | Outcome in Study |
| :--- | :--- | :--- |
| **H1** | LST relative to the rural reference rises along the ladder, but the magnitude depends on the reference definition and may be small or negative by day where rural land is bare. | **Supported (with nuance).** Daytime urban centres are cooler than pooled rural land in Hyderabad and Bengaluru; restricting the rural reference to vegetated land shifts all urban classes upward and flips Bengaluru positive. |
| **H2** | The built-up–LST relationship is nonlinear, with possible thresholds. | **Not supported out-of-sample.** Although fitted splines show local curvature, replacing a linear built-up term with a nonlinear spline adds negligible spatial cross-validated predictive skill ($|\Delta R^2| \le 0.0023$) across all five cities. |
| **H3** | Vegetation moderates the built-up–LST relationship. | **Untestable empirically.** Dense urban cells almost never overlap with the city-wide interquartile range of vegetation greenness ($0.0\%\text{–}3.3\%$ coverage vs. a $5\%$ minimum threshold), preventing model-free testing without extrapolation. |
| **H4** | The shape and magnitude of relationships differ across cities. | **Supported.** Urban–rural contrast signs, curve slopes, and total explained variance diverge substantially across the five cities. |
| **H5** | NDBI partly captures bare-soil and dryness effects, distorting estimated relationships. | **Supported.** Across all five cities, NDBI correlates far more strongly with LST and bare soil than with physical built-up fraction, whereas three independent physical built-up datasets agree closely with one another. |
| **H6** | The built-up–LST response differs by urban context at the same built fraction. | **Supported.** At identical built-up fractions ($0.15\text{–}0.35$) and fixed vegetation levels, different settlement classes exhibit distinct relative temperatures. |
| **H7** | Built-up age or trajectory adds explanatory information after current built-up fraction. | **Not tested.** Excluded alongside RQ3. |

---

## 2. Study Design and Step-by-Step Methodology

Every city was processed independently using an identical, unpooled workflow so that cross-city comparisons reflect genuine regional differences rather than pooled-sample averaging.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Harmonised Spatial Grid & Settlement Ladder (Static Base)            │
│ • 50 km radius around each city centre → 334 × 334 grid of 300 m cells        │
│   (EPSG:7755 projected metres; ~87,000 non-water land cells per city)        │
│ • GHSL SMOD 2020 ladder: Rural (11–13), Suburban (21), Semi-dense (22),      │
│   Dense (23), Urban Centre (30); Water (10) & JRC Water (>50%) excluded      │
│ • Physical built-up fraction: GHS-BUILT-S 2020 (aggregated 100 m → 300 m)    │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Pre-Monsoon Satellite Composites (2022, 2023, 2025; March–May)       │
│ • Landsat 8/9 Collection 2 Level 2 (~10:30 AM local overpass)                │
│ • Seasonal medians of Land Surface Temperature (LST, K) and NDVI             │
│ • Quality screening: QA_PIXEL cloud/shadow/cirrus mask, thermal uncertainty  │
│   ST_QA ≤ 5 K, ≥ 3 clear observations/cell, ≤ 10% missing LST per city-year  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Relative Temperature Panel Construction                              │
│ • Relative LST: lst_rel(i, t) = LST(i, t) − median_LST(Rural 11–13, t)       │
│ • Removes interannual synoptic background shifts within each city-year       │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Spatial-Block Uncertainty & Modelling Framework                      │
│ • 5 km × 5 km spatial blocks (projected metres, fixed across years)          │
│ • Class-ladder gradients: 1,000-draw 5 km block bootstrap (95% CIs)          │
│ • Nonlinear response models: GAMs with 5-fold 5 km spatial GroupKFold CV     │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Targeted Sensitivity Experiments (RQ1 & RQ2 Completions)             │
│ • Exp A (RQ1): Compare pooled rural (Ref_A) vs low-density rural (Ref_B)     │
│   vs vegetated rural (Ref_C) across all 5 cities                             │
│ • Exp B (RQ2 Parts A & B): Within-context smooths (H6) & linear vs nonlinear │
│   CV comparison (H2)                                                         │
│ • Exp C (RQ2 Part C): Extract Landsat NDBI, Dynamic World built, & ESA       │
│   WorldCover built onto the 300 m grid to test metric bias (H5)              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Summary of Procedures

1. **Grid & Land-Cover Harmonisation:** Each metropolitan region was bounded by a $50\text{ km}$ circle subdivided into $300\text{ m} \times 300\text{ m}$ cells in a metric Indian projection (`EPSG:7755`). Permanent surface water (JRC Global Surface Water occurrence $>50\%$ and GHSL class 10) was masked out. Each land cell received its 2020 GHSL Degree of Urbanisation (SMOD) class and continuous built-up surface fraction (`GHS-BUILT-S`).
2. **Pre-Monsoon Thermal & Vegetation Extraction:** Pre-monsoon ($1\text{ March}\text{–}31\text{ May}$) Landsat 8/9 scenes were composited for 2022, 2023, and 2025. Thermal uncertainty filtering ($\text{ST\_QA} \le 5\text{ K}$, raised from an initial $3\text{ K}$ threshold after diagnostic checks showed $3\text{ K}$ discarded over $90\%$ of clear pixels in coastal Chennai) preserved $89\%\text{–}100\%$ spatial coverage across all city-years.
3. **Relative Surface Temperature ($\text{lst\_rel}$):** To isolate intra-urban thermal gradients from year-to-year regional heat fluctuations, each cell's LST was expressed relative to the median LST of its city's rural cells (`SMOD 11–13`) in that same year.
4. **Spatial-Block Inference:** Because adjacent $300\text{ m}$ pixels are strongly autocorrelated, all confidence intervals and cross-validation splits were grouped by **$5\text{ km}$ spatial blocks**. Class-level medians were evaluated using $1,000$ block-bootstrap resamples, while continuous surface-response GAMs ($\text{lst\_rel} \sim s(\text{built}) + s(\text{ndvi}) + te(\text{built}, \text{ndvi}) + f(\text{year})$) were fit on $10,000$-cell random subsamples and scored using 5-fold spatial `GroupKFold` cross-validation.
5. **Three Sensitivity Experiments:**
   * **Rural Baseline Definitions (RQ1):** Recomputed all class gradients after redefining the rural baseline as very-low-density rural only (`Ref_B`: $\text{SMOD} == 11$) and vegetated low-built rural (`Ref_C`: `SMOD 11–13` with $\text{built} < 0.05$ and $\text{NDVI} \ge \text{city-year rural median}$).
   * **Within-Context Smooths & Linearity Test (RQ2 Parts A & B):** Fit separate smooths inside each eligible SMOD class ($\ge 500$ cells and $\ge 30$ blocks) to compare temperature at overlapping built-up fractions ($0.15, 0.25, 0.35$), and compared the full nonlinear GAM against a linear built-up specification on identical spatial CV folds.
   * **Built-Up Metric Comparison (RQ2 Part C):** Extracted March–May Landsat NDBI (with positive surface-reflectance masking $\text{SR\_B4}, \text{SR\_B5}, \text{SR\_B6} > 0$ to prevent negative-reflectance denominator blow-ups), March–May Google Dynamic World built probability, and ESA WorldCover 2021 built-up fraction onto the exact $300\text{ m}$ grid, comparing their correlations and spatial CV predictive power.

---

## 3. Empirical Results Across the Five Cities

### 3.1 Baseline Urban–Rural Ladder & Rural Reference Sensitivity (RQ1 / H1, H4)

Under the standard pooled rural baseline (`Ref_A`: SMOD `11–13`), mid-morning urban centres (`class 30`) do **not** exhibit a uniform urban heat island:

* **Consistent Daytime Urban Cool Islands:** **Hyderabad** ($-2.22\text{ K}$, $-1.68\text{ K}$, $-1.98\text{ K}$) and **Bengaluru** ($-1.04\text{ K}$, $-1.00\text{ K}$, $-0.94\text{ K}$) are cooler in their urban centres than in surrounding rural land across all three years.
* **Warm, Neutral, and Interannually Variable Cities:** **Kolkata** is consistently warmer in its centre ($+0.38\text{ K}$, $+0.20\text{ K}$, $+0.41\text{ K}$), **Chennai** is near neutral ($-0.06\text{ K}$, $+0.54\text{ K}$, $+0.04\text{ K}$), and **Delhi** shifts from slightly cool in 2022 ($-0.30\text{ K}$) to distinctly warm in 2025 ($+1.01\text{ K}$).

Redefining the rural baseline reveals why: restricting the rural reference to **vegetated, low-built rural land (`Ref_C`)** lowers the rural baseline LST by **$0.56\text{ K}$ to $2.18\text{ K}$** in every city-year (smallest in humid Kolkata, largest in Bengaluru, Delhi, Chennai, and Hyderabad). Because $\text{lst\_rel} = \text{LST}_{\text{cell}} - \text{LST}_{\text{rural}}$, subtracting a cooler vegetated rural baseline shifts every urban class upward:

#### Table 1: Urban Centre (`Class 30`) Median $\text{lst\_rel}$ ($\text{K}$) Across Rural Reference Definitions
*(Values in brackets denote 95% $5\text{ km}$ spatial-block bootstrap confidence intervals)*

| City | Year | `Ref_C − Ref_A` Rural Shift ($\text{K}$) | `Ref_A`: Pooled Rural (`11–13`) | `Ref_B`: Low-Density Rural (`11` only) | `Ref_C`: Vegetated Rural ($\text{NDVI} \ge \text{med}$, $\text{built} < 0.05$) | Sign Flip Under `Ref_C`? |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Delhi** | 2022 | $-2.164$ | $-0.30\ [-1.07, +0.40]$ | $+0.22\ [-0.53, +0.87]$ | $+1.87\ [+1.43, +2.27]$ | Yes (flips at `Ref_B` & `Ref_C`) |
| **Delhi** | 2023 | $-1.944$ | $+0.14\ [-0.30, +0.62]$ | $+0.55\ [+0.07, +1.10]$ | $+2.08\ [+1.69, +2.45]$ | No (positive in all) |
| **Delhi** | 2025 | $-1.244$ | $+1.01\ [+0.61, +1.42]$ | $+1.41\ [+0.94, +1.82]$ | $+2.26\ [+1.91, +2.56]$ | No (positive in all) |
| **Hyderabad** | 2022 | $-1.663$ | $-2.22\ [-2.63, -1.75]$ | $-2.20\ [-2.65, -1.70]$ | $-0.55\ [-0.99, -0.10]$ | No (shrinks by $1.67\text{ K}$) |
| **Hyderabad** | 2023 | $-1.816$ | $-1.68\ [-2.03, -1.33]$ | $-1.70\ [-2.10, -1.31]$ | $+0.14\ [-0.19, +0.45]$ | Yes (crosses zero) |
| **Hyderabad** | 2025 | $-1.703$ | $-1.98\ [-2.31, -1.64]$ | $-2.13\ [-2.48, -1.75]$ | $-0.28\ [-0.62, +0.03]$ | No (overlaps zero) |
| **Kolkata** | 2022 | $-0.561$ | $+0.38\ [+0.10, +0.68]$ | $+0.60\ [+0.24, +0.99]$ | $+0.94\ [+0.67, +1.22]$ | No (positive in all) |
| **Kolkata** | 2023 | $-0.670$ | $+0.20\ [-0.19, +0.63]$ | $+0.09\ [-0.38, +0.70]$ | $+0.87\ [+0.47, +1.31]$ | No (positive in all) |
| **Kolkata** | 2025 | $-1.096$ | $+0.41\ [+0.09, +0.70]$ | $+0.74\ [+0.24, +1.21]$ | $+1.50\ [+1.22, +1.78]$ | No (positive in all) |
| **Chennai** | 2022 | $-1.968$ | $-0.06\ [-0.76, +0.58]$ | $-0.04\ [-0.87, +0.75]$ | $+1.91\ [+1.26, +2.54]$ | Yes (flips strongly positive) |
| **Chennai** | 2023 | $-1.686$ | $+0.54\ [+0.15, +0.97]$ | $+0.74\ [+0.26, +1.27]$ | $+2.22\ [+1.89, +2.60]$ | No (positive in all) |
| **Chennai** | 2025 | $-1.836$ | $+0.04\ [-0.43, +0.50]$ | $+0.20\ [-0.49, +0.78]$ | $+1.88\ [+1.54, +2.23]$ | No (positive in all) |
| **Bengaluru** | 2022 | $-1.731$ | $-1.04\ [-1.44, -0.59]$ | $-0.49\ [-0.94, +0.02]$ | $+0.69\ [+0.30, +1.12]$ | Yes (flips positive) |
| **Bengaluru** | 2023 | $-1.333$ | $-1.00\ [-1.38, -0.60]$ | $-0.51\ [-1.00, -0.00]$ | $+0.33\ [-0.08, +0.77]$ | Yes (flips positive) |
| **Bengaluru** | 2025 | $-2.176$ | $-0.94\ [-1.35, -0.49]$ | $-0.34\ [-0.82, +0.22]$ | $+1.23\ [+0.86, +1.64]$ | Yes (flips positive) |

*Key Takeaway:* **Bengaluru** flips from a daytime cool island into a daytime heat island in all three years once bare rural soil is excluded from the baseline, and **Hyderabad's** daytime cool island shrinks near zero.

---

### 3.2 Vegetation Dominance, Nonlinearity, and Context Dependence (RQ2 Parts A & B / H2, H3, H6)

1. **Vegetation Carries Most Explanatory Power:** Across 5-fold spatial CV, $\text{NDVI} + \text{year}$ achieves $R^2 = 0.305\text{–}0.546$, whereas $\text{built} + \text{year}$ alone has near-zero predictive skill in Delhi ($0.011$), Hyderabad ($0.007$), Chennai ($0.032$), and Bengaluru ($-0.003$), showing standalone skill only in Kolkata ($0.230$). Adding $\text{built}$ and $te(\text{built}, \text{ndvi})$ improves CV $R^2$ by $+0.031$ to $+0.129$ over $\text{NDVI} + \text{year}$.
2. **Vegetation Moderation at High Built Density Is Untestable (`H3`):** Because high-density urban cells ($\text{built} > 0.4$, only $2.9\%\text{–}7.0\%$ of cells) contain almost no pixels inside the city-wide NDVI interquartile range ($0.0\%$ overlap in Kolkata to $3.3\%$ in Bengaluru), fixed-NDVI contrasts at high built density require pure model extrapolation and cannot be tested empirically.
3. **Nonlinear Built-Up Terms Add Negligible Out-of-Sample Gain (`H2`):** Comparing $\text{lst\_rel} \sim \text{built} + s(\text{ndvi}) + f(\text{year})$ against $\text{lst\_rel} \sim s(\text{built}) + s(\text{ndvi}) + f(\text{year})$ on identical spatial folds shows virtually zero out-of-sample gain in every city:

#### Table 2: Spatial Cross-Validated $R^2$ — Baseline Models & Nonlinearity Test (`H2`)

| City | $\text{NDVI} + \text{year}$ CV $R^2$ | $\text{built} + \text{year}$ CV $R^2$ | Full GAM CV $R^2$ | Linear Built ($\text{built} + s(\text{ndvi}) + \text{year}$) | Nonlinear Built ($s(\text{built}) + s(\text{ndvi}) + \text{year}$) | Nonlinear Gain ($\Delta R^2$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Delhi** | $0.305$ | $0.011$ | $0.356$ | $0.3521$ | $0.3498$ | $-0.0023$ |
| **Hyderabad** | $0.546$ | $0.007$ | $0.637$ | $0.6228$ | $0.6233$ | $+0.0005$ |
| **Kolkata** | $0.332$ | $0.230$ | $0.461$ | $0.4233$ | $0.4235$ | $+0.0002$ |
| **Chennai** | $0.430$ | $0.032$ | $0.461$ | $0.4396$ | $0.4396$ | $-0.0000$ |
| **Bengaluru** | $0.461$ | $-0.003$ | $0.553$ | $0.5393$ | $0.5395$ | $+0.0002$ |

4. **Urban Context Matters at Fixed Built-Up Density (`H6`):** Fitting smooths separately inside each eligible SMOD class (evaluated at city-median NDVI, year 2022) shows substantial temperature divergence across settlement contexts even when local $300\text{ m}$ built-up fraction is held constant:

#### Table 3: Within-Context Predicted $\text{lst\_rel}$ ($\text{K}$) at Overlapping Built-Up Fractions (`H6`)
*(Evaluated at city-median NDVI, year 2022; `n/a` indicates outside that class's 1st–99th percentile support; Chennai semi-dense excluded due to $<500$ cells / $<30$ blocks)*

| City | Built Fraction | Suburban (`21`) | Semi-Dense (`22`) | Dense (`23`) | Urban Centre (`30`) | Key Context Contrast |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Delhi** | `0.15` | $+0.72\ [+0.34, +1.17]$ | $+2.25\ [+1.29, +2.86]$ | $+0.48\ [-0.13, +0.97]$ | $+0.14\ [-0.17, +0.45]$ | Semi-dense is $+2.11\text{ K}$ warmer than centre |
| **Delhi** | `0.25` | $-0.02\ [-0.44, +0.41]$ | $+0.95\ [-0.08, +2.04]$ | $+0.19\ [-0.27, +0.61]$ | $-0.14\ [-0.37, +0.12]$ | Semi-dense remains warmest |
| **Hyderabad** | `0.15` | $-1.50\ [-1.65, -1.23]$ | $-0.53\ [-0.90, +0.08]$ | $-1.46\ [-1.78, -0.92]$ | $-2.48\ [-2.80, -2.12]$ | Centre is $0.98\text{ K}$ cooler than suburban |
| **Hyderabad** | `0.25` | $-2.07\ [-2.26, -1.61]$ | $-1.28\ [-1.51, -0.44]$ | $-1.94\ [-2.29, -1.27]$ | $-2.94\ [-3.27, -2.55]$ | Centre remains coolest across all fractions |
| **Kolkata** | `0.15` | $+0.95\ [+0.63, +1.27]$ | $+0.21\ [-0.04, +0.51]$ | $+0.75\ [+0.45, +0.96]$ | $+0.95\ [+0.80, +1.12]$ | Centre & suburban $+0.74\text{ K}$ warmer than semi-dense |
| **Chennai** | `0.15` | $-0.63\ [-0.92, -0.35]$ | `n/a` | $-0.55\ [-1.04, -0.05]$ | $-0.91\ [-1.25, -0.56]$ | All eligible contexts slightly negative |
| **Bengaluru** | `0.15` | $-0.44\ [-0.60, -0.26]$ | $-0.06\ [-0.56, +0.47]$ | $-0.31\ [-0.75, +0.08]$ | $-1.32\ [-1.61, -0.98]$ | Centre is $0.88\text{ K}$ cooler than suburban |
| **Bengaluru** | `0.25` | $-1.11\ [-1.56, -0.74]$ | $+0.06\ [-0.52, +0.83]$ | $-0.91\ [-1.65, -0.24]$ | $-2.06\ [-2.32, -1.77]$ | Centre divergence widens to $0.95\text{ K}$ |

---

### 3.3 Built-Up Metric Sensitivity: NDBI vs. Physical Built-Up Datasets (RQ2 Part C / H5)

Comparing **GHS-BUILT-S**, **Landsat NDBI**, **Google Dynamic World (`built`)**, and **ESA WorldCover (`class 50`)** across all five cities confirms **H5**:

* **NDBI Tracks Bare Soil and LST Rather Than Buildings:** NDBI correlates weakly—and even negatively—with physical built-up fraction ($r = -0.17$ to $+0.30$), but correlates strongly with bare-soil proxies ($r = 0.56\text{–}0.60$ in Kolkata, Chennai, Delhi, and Bengaluru) and $\text{lst\_rel}$ ($r = -0.351$ in Hyderabad; $+0.583$ to $+0.786$ in the remaining four cities).
* **Physical Built-Up Datasets Agree:** `GHS-BUILT-S`, `Dynamic World`, and `ESA WorldCover` exhibit nearly identical predictive behavior—near-zero standalone CV $R^2$ when paired only with year, rising to $0.33\text{–}0.64$ only once $\text{NDVI}$ and interaction terms are introduced.

#### Table 4: Cross-Metric Spearman Correlations and 5-Fold Spatial CV $R^2$ (`H5`)

| City | Metric | Spearman $r$ with $\text{lst\_rel}$ | Spearman $r$ with `GHS-BUILT-S` | Spearman $r$ with Bare-Soil Proxy | Linear CV $R^2$ ($\text{metric} + \text{year}$) | Full GAM CV $R^2$ ($\text{metric} + \text{NDVI} + \text{int.} + \text{year}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Hyderabad** | `GHS-BUILT-S` | $-0.136$ | $1.000$ | — | $0.0074$ | $0.6373$ |
| | `Landsat NDBI` | **$-0.351$** | $-0.146$ | $-0.261$ | **$0.4035$** | $0.6293$ |
| | `Dynamic World` | $-0.105$ | $+0.754$ | $+0.125$ | $0.0032$ | $0.6381$ |
| | `ESA WorldCover` | $-0.139$ | $+0.526$ | $+0.237$ | $0.0042$ | $0.6125$ |
| **Kolkata** | `GHS-BUILT-S` | $+0.324$ | $1.000$ | — | $0.2303$ | $0.4605$ |
| | `Landsat NDBI` | **$+0.654$** | $+0.298$ | **$+0.593$** | **$0.4840$** | $0.5484$ |
| | `Dynamic World` | $+0.324$ | — | $+0.179$ | $0.1848$ | $0.4582$ |
| | `ESA WorldCover` | $+0.380$ | — | $+0.273$ | $0.1740$ | $0.4408$ |
| **Chennai** | `GHS-BUILT-S` | $+0.165$ | $1.000$ | — | $0.0310$ | $0.4608$ |
| | `Landsat NDBI` | **$+0.786$** | $+0.054$ | **$+0.564$** | **$0.6558$** | $0.7072$ |
| | `Dynamic World` | $+0.225$ | — | $+0.264$ | $0.0613$ | $0.4801$ |
| | `ESA WorldCover` | $+0.159$ | — | $+0.342$ | $0.0216$ | $0.4466$ |
| **Delhi** | `GHS-BUILT-S` | $+0.165$ | $1.000$ | — | $0.0064$ | $0.3565$ |
| | `Landsat NDBI` | **$+0.583$** | $-0.167$ | **$+0.597$** | **$0.3952$** | $0.4344$ |
| | `Dynamic World` | $+0.026$ | — | $-0.059$ | $0.0385$ | $0.3541$ |
| | `ESA WorldCover` | $+0.125$ | — | $+0.179$ | $-0.0009$ | $0.3341$ |
| **Bengaluru** | `GHS-BUILT-S` | $-0.028$ | $1.000$ | — | $-0.0049$ | $0.5528$ |
| | `Landsat NDBI` | **$+0.716$** | $-0.118$ | **$+0.581$** | **$0.5463$** | $0.6528$ |
| | `Dynamic World` | $-0.003$ | — | $+0.244$ | $0.0144$ | $0.5659$ |
| | `ESA WorldCover` | $-0.089$ | — | $+0.258$ | $-0.0090$ | $0.5281$ |

---

## 4. Methodological Scope, Limitations, and Claims Boundaries

To maintain strict scientific rigor in the manuscript, conclusions are bounded by the following design constraints:

* **Observational Associations Only:** All findings represent spatial and interannual associations across satellite snapshots rather than causal effects. Cross-city comparisons are descriptive across five independently modelled metropolitan regions.
* **Mid-Morning Land Surface Temperature vs. Air Temperature:** Landsat 8/9 captures radiative skin temperature at approximately 10:30 AM local time. Results do not represent afternoon peak canopy air temperature, nighttime heat retention, or human thermal comfort.
* **Scale Mismatch & Support Limits:** GHSL SMOD classes are defined at $1\text{ km}$ resolution and mapped onto $300\text{ m}$ cells, representing neighbourhood settlement context rather than single-parcel morphology. Furthermore, built-up fractions above $0.40$ represent only $2.9\%\text{–}7.0\%$ of cells in any city, bounding high-density curve interpretation.
* **Post-Hoc Analytical Conventions:** Several operational thresholds—including the $5\text{ K}$ `ST_QA` thermal uncertainty filter, the $5\%$ NDVI overlap gate, the vegetated rural baseline (`Ref_C`), and positive surface-reflectance masking for NDBI—were established during diagnostic validation and will be explicitly reported as study conventions in the Methods section.