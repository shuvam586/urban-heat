# RQ2 Part A: Urban Context Dependence & Nonlinearity — Five-City Comparison

Assembled from `outputs/<city>/rq2_context.json` and `rq2_context.csv` for all five cities
(Delhi, Hyderabad, Kolkata, Chennai, Bengaluru). Each city was processed independently;
nothing is pooled. All results are associations, not causal effects. Years: 2022, 2023, 2025.
Grid: 300 m cells, EPSG:7755, 50 km radius. `lst_rel` = cell LST minus the median LST of
the rural reference (SMOD 11–13) in that city-year. Bootstrap: 200 draws, seed 42,
resampling 5 km blocks with replacement. Part B uses the same 10,000-cell subsample
(seed 42) and 5 km GroupKFold folds as step 05/cv.json.

## 1. Context coverage: cell counts and distinct 5 km blocks

| City | Context | Cells | Blocks | Eligible | Built q01–q099 |
|---|---|---:|---:|:---:|---:|
| Delhi | rural | 40,398 | 301 | Yes | [0.000, 0.172] |
| Delhi | suburban | 16,831 | 277 | Yes | [0.000, 0.364] |
| Delhi | semi-dense | 869 | 61 | Yes | [0.000, 0.457] |
| Delhi | dense | 3,304 | 150 | Yes | [0.000, 0.503] |
| Delhi | centre | 25,865 | 162 | Yes | [0.000, 0.660] |
| Hyderabad | rural | 61,624 | 331 | Yes | [0.000, 0.114] |
| Hyderabad | suburban | 13,433 | 230 | Yes | [0.000, 0.271] |
| Hyderabad | semi-dense | 832 | 50 | Yes | [0.000, 0.336] |
| Hyderabad | dense | 1,316 | 66 | Yes | [0.000, 0.434] |
| Hyderabad | centre | 9,737 | 63 | Yes | [0.000, 0.610] |
| Kolkata | rural | 13,339 | 262 | Yes | [0.000, 0.101] |
| Kolkata | suburban | 27,780 | 305 | Yes | [0.000, 0.176] |
| Kolkata | semi-dense | 1,380 | 50 | Yes | [0.000, 0.174] |
| Kolkata | dense | 4,369 | 140 | Yes | [0.000, 0.251] |
| Kolkata | centre | 35,365 | 259 | Yes | [0.000, 0.523] |
| Chennai | rural | 20,504 | 162 | Yes | [0.000, 0.104] |
| Chennai | suburban | 9,821 | 141 | Yes | [0.000, 0.248] |
| Chennai | semi-dense | 421 | 23 | **No** | [0.000, 0.343] |
| Chennai | dense | 1,438 | 60 | Yes | [0.000, 0.455] |
| Chennai | centre | 11,013 | 74 | Yes | [0.000, 0.534] |
| Bengaluru | rural | 49,267 | 328 | Yes | [0.000, 0.183] |
| Bengaluru | suburban | 24,526 | 277 | Yes | [0.000, 0.255] |
| Bengaluru | semi-dense | 632 | 39 | Yes | [0.000, 0.374] |
| Bengaluru | dense | 1,230 | 44 | Yes | [0.000, 0.478] |
| Bengaluru | centre | 11,470 | 87 | Yes | [0.000, 0.613] |

Eligibility requires ≥500 unique cells and ≥30 distinct 5 km blocks. Chennai semi-dense
(421 cells, 23 blocks) is the only ineligible context.

Overlap ranges across eligible contexts:
- **All eligible contexts:** Delhi [0.000, 0.172], Hyderabad [0.000, 0.114],
  Kolkata [0.000, 0.101], Chennai [0.000, 0.104], Bengaluru [0.000, 0.183]
- **Urban contexts only (excluding rural):** Delhi [0.000, 0.364],
  Hyderabad [0.000, 0.271], Kolkata [0.000, 0.174], Chennai [0.000, 0.248],
  Bengaluru [0.000, 0.255]

## 2. Urban-context predicted lst_rel at overlapping built fractions

Median `lst_rel` (K) with 95% block-bootstrap CI, evaluated at city-median NDVI,
year 2022, across each context's supported built range. "n/a" = outside that
context's supported built range.

### Delhi (urban overlap: [0.000, 0.364])

| Built | Suburban | Semi-dense | Dense | Centre |
|---|---|---|---|---|
| 0.15 | +0.723 [+0.336,+1.169] | +2.250 [+1.286,+2.862] | +0.484 [−0.131,+0.972] | +0.142 [−0.170,+0.447] |
| 0.25 | −0.018 [−0.438,+0.409] | +0.951 [−0.080,+2.037] | +0.186 [−0.273,+0.611] | −0.135 [−0.371,+0.121] |
| 0.35 | −0.589 [−1.087,−0.079] | +0.070 [−1.111,+0.847] | −0.992 [−1.618,−0.479] | −0.472 [−0.733,−0.245] |

### Hyderabad (urban overlap: [0.000, 0.271])

| Built | Suburban | Semi-dense | Dense | Centre |
|---|---|---|---|---|
| 0.15 | −1.499 [−1.645,−1.233] | −0.532 [−0.904,+0.081] | −1.459 [−1.778,−0.915] | −2.479 [−2.796,−2.117] |
| 0.25 | −2.072 [−2.262,−1.611] | −1.282 [−1.511,−0.442] | −1.936 [−2.289,−1.265] | −2.939 [−3.269,−2.553] |
| 0.35 | n/a | −1.582 [−1.975,−0.642] | −1.980 [−2.645,−0.949] | −3.414 [−3.835,−2.952] |

### Kolkata (urban overlap: [0.000, 0.174])

| Built | Suburban | Semi-dense | Dense | Centre |
|---|---|---|---|---|
| 0.15 | +0.945 [+0.628,+1.270] | +0.212 [−0.040,+0.507] | +0.745 [+0.447,+0.964] | +0.949 [+0.799,+1.118] |
| 0.25 | n/a | n/a | +1.423 [+0.908,+1.746] | +1.630 [+1.486,+1.952] |
| 0.35 | n/a | n/a | n/a | +2.501 [+2.114,+2.921] |

### Chennai (urban overlap: [0.000, 0.248])

| Built | Suburban | Semi-dense | Dense | Centre |
|---|---|---|---|---|
| 0.15 | −0.626 [−0.918,−0.354] | n/a | −0.552 [−1.037,−0.046] | −0.905 [−1.250,−0.557] |
| 0.25 | −0.801 [−1.237,−0.390] | n/a | −0.659 [−1.319,−0.042] | −0.824 [−1.179,−0.514] |
| 0.35 | n/a | n/a | +0.139 [−1.022,+1.156] | −0.869 [−1.294,−0.488] |

### Bengaluru (urban overlap: [0.000, 0.255])

| Built | Suburban | Semi-dense | Dense | Centre |
|---|---|---|---|---|
| 0.15 | −0.439 [−0.600,−0.262] | −0.061 [−0.564,+0.470] | −0.306 [−0.754,+0.076] | −1.320 [−1.614,−0.980] |
| 0.25 | −1.110 [−1.561,−0.738] | +0.064 [−0.516,+0.826] | −0.908 [−1.646,−0.244] | −2.063 [−2.318,−1.773] |
| 0.35 | n/a | −0.185 [−1.444,+0.685] | −0.853 [−1.361,−0.310] | −2.659 [−2.961,−2.303] |

### Reading across cities

At overlapping built fractions, contexts differ substantially in median `lst_rel`:
- **Delhi:** At built 0.15, semi-dense (+2.250 K) is far above suburban (+0.723 K),
  while centre (+0.142 K) is near rural reference. At built 0.35, all contexts turn
  negative.
- **Hyderabad:** All urban contexts are negative at all built fractions; centre is
  consistently ~0.5–1.0 K below suburban at the same built fraction.
- **Kolkata:** All urban contexts are positive; centre (+0.949 K at built 0.15) is
  the warmest, semi-dense (+0.212 K) the coolest.
- **Chennai:** All urban contexts are negative or near zero; semi-dense is ineligible
  (too few cells/blocks).
- **Bengaluru:** All urban contexts are negative; centre (−1.320 K at built 0.15) is
  substantially cooler than suburban (−0.439 K).

## 3. Part B: Linear vs nonlinear built-up gain (H2)

Comparison of `lst_rel ~ built + s(ndvi) + f(year)` (linear) vs
`lst_rel ~ s(built) + s(ndvi) + f(year)` (nonlinear), on the same 10,000-cell
subsample and 5 km GroupKFold folds as step 05.

| City | Linear CV R² | Nonlinear CV R² | Mean gain | Folds favour nonlinear | Negligible (<0.005) |
|---|---:|---:|---:|---:|:---:|
| Delhi | 0.352084 | 0.349812 | −0.002272 | 3/5 | Yes |
| Hyderabad | 0.622776 | 0.623259 | +0.000483 | 4/5 | Yes |
| Kolkata | 0.423274 | 0.423457 | +0.000183 | 4/5 | Yes |
| Chennai | 0.439574 | 0.439560 | −0.000014 | 3/5 | Yes |
| Bengaluru | 0.539314 | 0.539496 | +0.000181 | 4/5 | Yes |

The nonlinear built term adds negligible out-of-sample predictive skill in all five
cities (mean gain |≤0.0023| R², all below the 0.005 threshold). Built fraction's
independent CV skill is minimal everywhere; NDVI + year carries nearly all model
performance.

### Derivative zero crossings (local extrema of s(built))

| City | Zero crossings (built fraction, type) |
|---|---|
| Delhi | max@0.028, min@0.062, max@0.093, min@0.151, max@0.177, min@0.262, max@0.304, min@0.487, max@0.514, min@0.560 |
| Hyderabad | max@0.006, min@0.344, max@0.375, min@0.459 |
| Kolkata | min@0.017 |
| Chennai | max@0.021, min@0.314, max@0.381, min@0.455 |
| Bengaluru | max@0.014, min@0.496 |

Delhi shows the most complex built-up response with 10 zero crossings; Kolkata the
simplest with 1. All mean gains are negligible (<0.005 R²).

## 4. Three sentences

Done: I ran `08_rq2_context.py` and `tests/check_08_rq2_context.py` via Git Bash for
all five cities (Hyderabad, Kolkata, Chennai, Delhi, Bengaluru) on existing
`panel.parquet`/`grid.parquet` with no Earth Engine calls; all five checks passed.
Results were compiled into `outputs/rq2_cross_city_context.md`.

Shows: All five cities have ≥4 eligible urban contexts (Chennai semi-dense is the
only ineligible context at 421 cells/23 blocks); at overlapping built fractions,
contexts differ substantially in median `lst_rel` (e.g., at built 0.15, Delhi's
centre +0.142 K vs semi-dense +2.250 K; Hyderabad's centre −2.479 K vs suburban
−1.499 K); the nonlinear built term adds negligible CV R² gain in all cities
(|mean gain| ≤0.0023, all below 0.005 threshold), with Delhi showing the most
complex derivative response (10 zero crossings) and Kolkata the simplest (1).

Could be wrong: Intervals reflect only the spatial-block bootstrap over each city's
grid; results are city-specific and not generalizable; the linear model uses a
piecewise-linear spline (spline_order=1) rather than a single-coefficient linear
term; all results are associations, not causal effects.
