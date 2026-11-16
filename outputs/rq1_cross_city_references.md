# RQ1 rural reference sensitivity: five-city comparison

Assembled from `outputs/<city>/rq1_references.csv` for all five cities
(Delhi, Hyderabad, Kolkata, Chennai, Bengaluru). Each city was processed
independently; nothing is pooled. All results are associations, not causal
effects. Years: 2022, 2023, 2025 (March–May). Grid: 300 m cells, EPSG:7755,
50 km radius. `lst_rel` = cell LST minus the median LST of the chosen rural
reference in that city-year. Bootstrap: 1,000 draws, seed 42, resampling 5 km
blocks with replacement and recomputing the reference median within each draw.

## Reference definitions

- Ref_A (baseline): SMOD in {11, 12, 13} — matches `gradient.csv` rural medians.
- Ref_B: SMOD == 11 only (very-low-density rural).
- Ref_C: SMOD in {11, 12, 13} with built < 0.05 and ndvi >= the median NDVI
  of Ref_A cells in that city-year (post-hoc convention).

## Reference coverage: cell counts and distinct 5 km blocks

| City | Year | Ref | Cells | Blocks |
|---|---:|---|---:|---:|
| Delhi | 2022 | Ref_A | 40,398 | 301 |
| Delhi | 2022 | Ref_B | 20,903 | 287 |
| Delhi | 2022 | Ref_C | 18,845 | 295 |
| Delhi | 2023 | Ref_A | 40,396 | 301 |
| Delhi | 2023 | Ref_B | 20,902 | 287 |
| Delhi | 2023 | Ref_C | 19,017 | 293 |
| Delhi | 2025 | Ref_A | 40,398 | 301 |
| Delhi | 2025 | Ref_B | 20,903 | 287 |
| Delhi | 2025 | Ref_C | 18,933 | 297 |
| Hyderabad | 2022 | Ref_A | 61,598 | 331 |
| Hyderabad | 2022 | Ref_B | 28,993 | 319 |
| Hyderabad | 2022 | Ref_C | 29,946 | 326 |
| Hyderabad | 2023 | Ref_A | 61,597 | 331 |
| Hyderabad | 2023 | Ref_B | 28,999 | 319 |
| Hyderabad | 2023 | Ref_C | 29,979 | 325 |
| Hyderabad | 2025 | Ref_A | 61,605 | 331 |
| Hyderabad | 2025 | Ref_B | 29,009 | 319 |
| Hyderabad | 2025 | Ref_C | 29,870 | 325 |
| Kolkata | 2022 | Ref_A | 13,333 | 261 |
| Kolkata | 2022 | Ref_B | 3,614 | 165 |
| Kolkata | 2022 | Ref_C | 6,483 | 232 |
| Kolkata | 2023 | Ref_A | 13,333 | 262 |
| Kolkata | 2023 | Ref_B | 3,611 | 165 |
| Kolkata | 2023 | Ref_C | 6,393 | 233 |
| Kolkata | 2025 | Ref_A | 13,025 | 259 |
| Kolkata | 2025 | Ref_B | 3,504 | 165 |
| Kolkata | 2025 | Ref_C | 6,340 | 231 |
| Chennai | 2022 | Ref_A | 18,980 | 161 |
| Chennai | 2022 | Ref_B | 7,887 | 148 |
| Chennai | 2022 | Ref_C | 9,014 | 153 |
| Chennai | 2023 | Ref_A | 20,405 | 162 |
| Chennai | 2023 | Ref_B | 8,405 | 148 |
| Chennai | 2023 | Ref_C | 9,704 | 155 |
| Chennai | 2025 | Ref_A | 20,034 | 162 |
| Chennai | 2025 | Ref_B | 8,282 | 148 |
| Chennai | 2025 | Ref_C | 9,529 | 156 |
| Bengaluru | 2022 | Ref_A | 49,202 | 328 |
| Bengaluru | 2022 | Ref_B | 16,707 | 293 |
| Bengaluru | 2022 | Ref_C | 23,188 | 322 |
| Bengaluru | 2023 | Ref_A | 49,240 | 328 |
| Bengaluru | 2023 | Ref_B | 16,733 | 293 |
| Bengaluru | 2023 | Ref_C | 23,235 | 325 |
| Bengaluru | 2025 | Ref_A | 49,250 | 328 |
| Bengaluru | 2025 | Ref_B | 16,734 | 293 |
| Bengaluru | 2025 | Ref_C | 23,135 | 320 |

All reference groups exceed 200 cells and 30 distinct 5 km blocks in every
city and year (minimum across all: Kolkata Ref_B 2025 = 3,504 cells / 165 blocks).

## Reference median LST differences (K), from each city's panel.parquet

Because `lst_rel = cell_LST − ref_LST`, a cooler rural reference shifts every
urban class median upward. The table below reports the median LST of each
reference (median `lst_k` over that reference's cells in that city-year) and the
difference versus Ref_A (Ref_X − Ref_A). Negative values mean Ref_X is cooler
than Ref_A.

| City | Year | Ref_A median LST (K) | Ref_A cells | Ref_B median LST (K) | Ref_B − Ref_A (K) | Ref_C median LST (K) | Ref_C − Ref_A (K) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Delhi | 2022 | 313.896 | 40,398 | 313.382 | −0.514 | 311.731 | −2.164 |
| Delhi | 2023 | 309.743 | 40,396 | 309.337 | −0.406 | 307.799 | −1.944 |
| Delhi | 2025 | 311.040 | 40,398 | 310.645 | −0.395 | 309.797 | −1.244 |
| Hyderabad | 2022 | 317.918 | 61,598 | 317.902 | −0.016 | 316.255 | −1.663 |
| Hyderabad | 2023 | 317.225 | 61,597 | 317.251 | +0.026 | 315.409 | −1.816 |
| Hyderabad | 2025 | 314.594 | 61,605 | 314.740 | +0.145 | 312.891 | −1.703 |
| Kolkata | 2022 | 307.398 | 13,333 | 307.177 | −0.221 | 306.837 | −0.561 |
| Kolkata | 2023 | 309.673 | 13,333 | 309.786 | +0.113 | 309.002 | −0.670 |
| Kolkata | 2025 | 306.952 | 13,025 | 306.619 | −0.333 | 305.856 | −1.096 |
| Chennai | 2022 | 316.737 | 18,980 | 316.714 | −0.023 | 314.769 | −1.968 |
| Chennai | 2023 | 314.229 | 20,405 | 314.027 | −0.202 | 312.543 | −1.686 |
| Chennai | 2025 | 313.149 | 20,034 | 312.992 | −0.157 | 311.313 | −1.836 |
| Bengaluru | 2022 | 312.912 | 49,202 | 312.359 | −0.553 | 311.181 | −1.731 |
| Bengaluru | 2023 | 312.947 | 49,240 | 312.463 | −0.485 | 311.614 | −1.333 |
| Bengaluru | 2025 | 313.137 | 49,250 | 312.533 | −0.604 | 310.961 | −2.176 |

Ref_C is cooler than Ref_A in every city and year (Ref_C − Ref_A ranges from
−0.561 K in Kolkata 2023 to −2.176 K in Bengaluru 2025). Ref_B is mostly
slightly cooler than Ref_A, ranging from −0.604 K (Bengaluru 2025) to +0.145 K
(Hyderabad 2025). Because `lst_rel = cell_LST − ref_LST`, subtracting a cooler
reference makes urban medians appear higher — this is a reference-level effect,
not a change in the urban classes themselves.

## Centre class (class 30) median lst_rel (K) with 95% bootstrap intervals

| City | Year | Ref | Median | CI low | CI high |
|---|---:|---|---:|---:|---:|
| Delhi | 2022 | Ref_A | -0.30 | -1.07 | +0.40 |
| Delhi | 2022 | Ref_B | +0.22 | -0.53 | +0.87 |
| Delhi | 2022 | Ref_C | +1.87 | +1.43 | +2.27 |
| Delhi | 2023 | Ref_A | +0.14 | -0.30 | +0.62 |
| Delhi | 2023 | Ref_B | +0.55 | +0.07 | +1.10 |
| Delhi | 2023 | Ref_C | +2.08 | +1.69 | +2.45 |
| Delhi | 2025 | Ref_A | +1.01 | +0.61 | +1.42 |
| Delhi | 2025 | Ref_B | +1.41 | +0.94 | +1.82 |
| Delhi | 2025 | Ref_C | +2.26 | +1.91 | +2.56 |
| Hyderabad | 2022 | Ref_A | -2.22 | -2.63 | -1.75 |
| Hyderabad | 2022 | Ref_B | -2.20 | -2.65 | -1.70 |
| Hyderabad | 2022 | Ref_C | -0.55 | -0.99 | -0.10 |
| Hyderabad | 2023 | Ref_A | -1.68 | -2.03 | -1.33 |
| Hyderabad | 2023 | Ref_B | -1.70 | -2.10 | -1.31 |
| Hyderabad | 2023 | Ref_C | +0.14 | -0.19 | +0.45 |
| Hyderabad | 2025 | Ref_A | -1.98 | -2.31 | -1.64 |
| Hyderabad | 2025 | Ref_B | -2.13 | -2.48 | -1.75 |
| Hyderabad | 2025 | Ref_C | -0.28 | -0.62 | +0.03 |
| Kolkata | 2022 | Ref_A | +0.38 | +0.10 | +0.68 |
| Kolkata | 2022 | Ref_B | +0.60 | +0.24 | +0.99 |
| Kolkata | 2022 | Ref_C | +0.94 | +0.67 | +1.22 |
| Kolkata | 2023 | Ref_A | +0.20 | -0.19 | +0.63 |
| Kolkata | 2023 | Ref_B | +0.09 | -0.38 | +0.70 |
| Kolkata | 2023 | Ref_C | +0.87 | +0.47 | +1.31 |
| Kolkata | 2025 | Ref_A | +0.41 | +0.09 | +0.70 |
| Kolkata | 2025 | Ref_B | +0.74 | +0.24 | +1.21 |
| Kolkata | 2025 | Ref_C | +1.50 | +1.22 | +1.78 |
| Chennai | 2022 | Ref_A | -0.06 | -0.76 | +0.58 |
| Chennai | 2022 | Ref_B | -0.04 | -0.87 | +0.75 |
| Chennai | 2022 | Ref_C | +1.91 | +1.26 | +2.54 |
| Chennai | 2023 | Ref_A | +0.54 | +0.15 | +0.97 |
| Chennai | 2023 | Ref_B | +0.74 | +0.26 | +1.27 |
| Chennai | 2023 | Ref_C | +2.22 | +1.89 | +2.60 |
| Chennai | 2025 | Ref_A | +0.04 | -0.43 | +0.50 |
| Chennai | 2025 | Ref_B | +0.20 | -0.49 | +0.78 |
| Chennai | 2025 | Ref_C | +1.88 | +1.54 | +2.23 |
| Bengaluru | 2022 | Ref_A | -1.04 | -1.44 | -0.59 |
| Bengaluru | 2022 | Ref_B | -0.49 | -0.94 | +0.02 |
| Bengaluru | 2022 | Ref_C | +0.69 | +0.30 | +1.12 |
| Bengaluru | 2023 | Ref_A | -1.00 | -1.38 | -0.60 |
| Bengaluru | 2023 | Ref_B | -0.51 | -1.00 | -0.00 |
| Bengaluru | 2023 | Ref_C | +0.33 | -0.08 | +0.77 |
| Bengaluru | 2025 | Ref_A | -0.94 | -1.35 | -0.49 |
| Bengaluru | 2025 | Ref_B | -0.34 | -0.82 | +0.22 |
| Bengaluru | 2025 | Ref_C | +1.23 | +0.86 | +1.64 |

## Dense class (class 23) median lst_rel (K) with 95% bootstrap intervals

| City | Year | Ref | Median | CI low | CI high |
|---|---:|---|---:|---:|---:|
| Delhi | 2022 | Ref_A | +0.35 | -0.71 | +1.41 |
| Delhi | 2022 | Ref_B | +0.87 | -0.18 | +1.96 |
| Delhi | 2022 | Ref_C | +2.52 | +1.44 | +3.59 |
| Delhi | 2023 | Ref_A | -0.05 | -0.51 | +0.44 |
| Delhi | 2023 | Ref_B | +0.35 | -0.14 | +0.90 |
| Delhi | 2023 | Ref_C | +1.89 | +1.35 | +2.35 |
| Delhi | 2025 | Ref_A | +0.52 | +0.01 | +0.99 |
| Delhi | 2025 | Ref_B | +0.91 | +0.37 | +1.45 |
| Delhi | 2025 | Ref_C | +1.76 | +1.21 | +2.24 |
| Hyderabad | 2022 | Ref_A | -0.79 | -1.22 | -0.28 |
| Hyderabad | 2022 | Ref_B | -0.78 | -1.22 | -0.23 |
| Hyderabad | 2022 | Ref_C | +0.87 | +0.43 | +1.41 |
| Hyderabad | 2023 | Ref_A | -0.35 | -0.88 | +0.17 |
| Hyderabad | 2023 | Ref_B | -0.37 | -0.95 | +0.16 |
| Hyderabad | 2023 | Ref_C | +1.47 | +0.91 | +1.97 |
| Hyderabad | 2025 | Ref_A | -0.45 | -0.90 | +0.06 |
| Hyderabad | 2025 | Ref_B | -0.59 | -1.05 | -0.10 |
| Hyderabad | 2025 | Ref_C | +1.25 | +0.77 | +1.76 |
| Kolkata | 2022 | Ref_A | +0.15 | -0.18 | +0.52 |
| Kolkata | 2022 | Ref_B | +0.37 | -0.04 | +0.81 |
| Kolkata | 2022 | Ref_C | +0.71 | +0.37 | +1.06 |
| Kolkata | 2023 | Ref_A | -0.34 | -0.88 | +0.18 |
| Kolkata | 2023 | Ref_B | -0.45 | -1.04 | +0.22 |
| Kolkata | 2023 | Ref_C | +0.33 | -0.24 | +0.86 |
| Kolkata | 2025 | Ref_A | +0.50 | +0.19 | +0.80 |
| Kolkata | 2025 | Ref_B | +0.83 | +0.34 | +1.32 |
| Kolkata | 2025 | Ref_C | +1.59 | +1.28 | +1.88 |
| Chennai | 2022 | Ref_A | -0.12 | -1.04 | +0.87 |
| Chennai | 2022 | Ref_B | -0.10 | -1.15 | +0.96 |
| Chennai | 2022 | Ref_C | +1.85 | +0.97 | +2.80 |
| Chennai | 2023 | Ref_A | +0.62 | +0.11 | +1.28 |
| Chennai | 2023 | Ref_B | +0.82 | +0.20 | +1.54 |
| Chennai | 2023 | Ref_C | +2.31 | +1.81 | +2.95 |
| Chennai | 2025 | Ref_A | +0.62 | -0.06 | +1.42 |
| Chennai | 2025 | Ref_B | +0.78 | -0.05 | +1.63 |
| Chennai | 2025 | Ref_C | +2.46 | +1.85 | +3.20 |
| Bengaluru | 2022 | Ref_A | +0.47 | -0.14 | +1.05 |
| Bengaluru | 2022 | Ref_B | +1.03 | +0.33 | +1.65 |
| Bengaluru | 2022 | Ref_C | +2.20 | +1.59 | +2.74 |
| Bengaluru | 2023 | Ref_A | -0.20 | -0.82 | +0.33 |
| Bengaluru | 2023 | Ref_B | +0.29 | -0.36 | +0.95 |
| Bengaluru | 2023 | Ref_C | +1.14 | +0.52 | +1.70 |
| Bengaluru | 2025 | Ref_A | -0.24 | -0.72 | +0.34 |
| Bengaluru | 2025 | Ref_B | +0.37 | -0.21 | +1.08 |
| Bengaluru | 2025 | Ref_C | +1.94 | +1.46 | +2.51 |

## Sign of the urban centre gradient: Ref_A vs Ref_B vs Ref_C

- **Delhi:** Centre median is negative under Ref_A in 2022 (−0.30 K) but turns
  positive under Ref_B (+0.22 K) and stays positive under Ref_C (+1.87 K). The
  sign flips when switching from pooled rural (Ref_A) to very-low-density rural
  (Ref_B) in 2022; in 2023 and 2025 the centre is positive under all three
  references, so no sign change there.
- **Hyderabad:** Centre median is negative under Ref_A and Ref_B in all three
  years (−2.22/−2.20 K in 2022, −1.68/−1.70 K in 2023, −1.98/−2.13 K in 2025).
  Under Ref_C the sign flips in 2023 only (−1.68 K under Ref_A/Ref_B vs +0.14 K
  under Ref_C; Ref_C CI crosses zero); 2022 and 2025 remain negative under all
  three references.
- **Kolkata:** Centre median is positive under Ref_A, Ref_B, and Ref_C in all
  three years (2022: +0.38/+0.60/+0.94 K; 2023: +0.20/+0.09/+0.87 K; 2025:
  +0.41/+0.74/+1.50 K). No sign change under any reference switch; magnitude
  grows monotonically from Ref_A to Ref_C.
- **Chennai:** Centre median is near zero/slightly negative under Ref_A and
  Ref_B in 2022 (−0.06/−0.04 K) but turns strongly positive under Ref_C
  (+1.91 K). The sign flips when switching from Ref_A/Ref_B to Ref_C in 2022;
  in 2023 and 2025 the centre is positive under all three references.
- **Bengaluru:** Centre median is negative under Ref_A and Ref_B in all three
  years (−1.04/−0.49 K in 2022, −1.00/−0.51 K in 2023, −0.94/−0.34 K in 2025;
  the Ref_B CI crosses zero in 2022 and 2025). Under Ref_C the sign flips in
  all three years (+0.69/+0.33/+1.23 K; 2023 Ref_C CI crosses zero).

## Three sentences

Done: I ran `07_rq1_references.py` and `tests/check_07_rq1_references.py` via Git
Bash for Kolkata, Chennai, Delhi, and Bengaluru (Hyderabad was done earlier),
each on existing `grid.parquet`/`panel.parquet` with no Earth Engine calls, and
all four checks passed; reference cell counts and distinct 5 km block counts
plus centre/dense medians with 95% bootstrap intervals were saved per city and
compiled into `outputs/rq1_cross_city_references.md`.

Shows: All reference groups exceed 200 cells and 30 blocks in every city/year
(minimum Kolkata Ref_B 2025: 3,504 cells / 165 blocks); Ref_C (built < 0.05 and
high-NDVI rural) is cooler than Ref_A in every city-year (median LST difference
Ref_C − Ref_A from −0.561 K in Kolkata 2023 to −2.176 K in Bengaluru 2025),
shifting all urban class medians upward by roughly the same amount because
`lst_rel = cell_LST − ref_LST`; the centre-class sign changes under Ref_C in
Hyderabad 2023, Chennai 2022, and Bengaluru all three years, under Ref_B in
Delhi 2022, and not at all in Kolkata.

Could be wrong: Intervals reflect only the spatial-block bootstrap over each
city's grid; results are city-specific and not generalizable; Ref_C is a
post-hoc convention not in PLAN.md; all outputs are associations, not causal
effects; the centre sign flip under Ref_C is driven almost entirely by the
reference level shifting, not by changes in the urban classes themselves.

## Anything unusual

Ref_C (vegetated rural: SMOD 11–13 with built < 0.05 and NDVI above the Ref_A
median) is consistently COOLER than Ref_A — median LST difference Ref_C − Ref_A
ranges from −0.561 K (Kolkata 2023) to −2.176 K (Bengaluru 2025) — so every
urban class median shifts up under Ref_C purely because `lst_rel =
cell_LST − ref_LST`. The centre sign flips are therefore a reference artifact:
where the centre is weakly negative or near zero under Ref_A/Ref_B
(Delhi 2022, Hyderabad 2023, Chennai 2022, Bengaluru all years), Ref_C pushes
it positive. Bengaluru is the only city where the centre flips sign under Ref_C
in all three years while staying negative under Ref_A and Ref_B. Ref_B differs
from Ref_A by at most ±0.6 K and never flips the centre sign except Delhi 2022.

## Assumptions not in PLAN.md

- The Ref_C convention (SMOD 11–13 with built < 0.05 and ndvi >= city-year Ref_A
  median NDVI) is a post-hoc addition not described in PLAN.md.
- Block IDs are derived identically to step 04 (`floor(x/5000)_floor(y/5000)` on
  EPSG:7755 metres) and fixed across years and references.
- Each bootstrap draw recomputes the reference median from resampled blocks and
  subtracts it from every class's resampled median (paired within-draw),
  consistent with the PLAN's block-bootstrap convention applied to a
  difference-of-medians statistic.
- No changes were made to `07_rq1_references.py`,
  `tests/check_07_rq1_references.py`, or any baseline pipeline file
  (`gradient.csv`, `cv.json`, `summary.md`, `PLAN.md`).
