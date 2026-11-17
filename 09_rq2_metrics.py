import argparse
import json
from pathlib import Path

import ee
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pygam import LinearGAM, f, s, te
from scipy.stats import spearmanr
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

import config

SUBSAMPLE_CELLS = 10000
SEED = 42
LAM_GRID = np.logspace(-1, 3, 5)
METRICS_FILENAME = "metrics.parquet"
GRID_SIZE = 334


def block_key_from_xy(x, y):
    key = (
        np.floor(x / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(y / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    return pd.factorize(key)[0]


def make_folds(sub, n_folds=config.CV_FOLDS):
    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    groups = block_key_from_xy(sub["x"].to_numpy(), sub["y"].to_numpy())
    splits = list(
        GroupKFold(n_splits=n_folds).split(X, y, groups)
    )
    return splits


def cv_scores(terms, X, y, splits, lam, valid):
    scores = []
    for train_index, test_index in splits:
        tr = train_index[valid[train_index]]
        te = test_index[valid[test_index]]
        fold = LinearGAM(terms, lam=lam)
        fold.fit(X[tr], y[tr])
        prediction = fold.predict(X[te])
        scores.append(float(r2_score(y[te], prediction)))
    return scores


def flatten_lam(value):
    if isinstance(value, (list, tuple, np.ndarray)):
        output = []
        for item in value:
            output.extend(flatten_lam(item))
        return output
    return [float(value)]


def flat_lam(lam):
    return flatten_lam(lam)[0]


def derivative_zero_crossings(gam, x_min, x_max, n_points=500):
    xs = np.linspace(x_min, x_max, n_points)
    X_eval = np.column_stack([xs, np.zeros(n_points), np.zeros(n_points)])
    pd_vals = gam.partial_dependence(term=0, X=X_eval)
    pd_vals = np.asarray(pd_vals).ravel()
    dx = xs[1] - xs[0]
    deriv = np.gradient(pd_vals, dx)
    second = np.gradient(deriv, dx)
    crossings = []
    for i in range(1, len(deriv) - 1):
        if deriv[i - 1] < 0 < deriv[i] or deriv[i - 1] > 0 > deriv[i]:
            xc = xs[i]
            xtype = "min" if second[i] > 0 else "max"
            crossings.append({"type": xtype, "built": float(xc)})
    return crossings


def compute_300_raw(image, bands, x_min, y_max):
    """Extract raw bands at 300m grid using computePixels (fast)."""
    result = ee.data.computePixels(
        {
            "expression": image,
            "fileFormat": "NUMPY_NDARRAY",
            "bandIds": bands,
            "grid": {
                "dimensions": {"width": GRID_SIZE, "height": GRID_SIZE},
                "affineTransform": {
                    "scaleX": 300,
                    "shearX": 0,
                    "translateX": x_min,
                    "shearY": 0,
                    "scaleY": -300,
                    "translateY": y_max,
                },
                "crsCode": config.GRID_CRS,
            },
        }
    )
    return {band: result[band] for band in bands}


def prep_landsat_raw(image):
    """Prepare Landsat image with raw bands (no masking in EE)."""
    qa = image.select(config.QA_PIXEL_BAND)
    cloud_bits = sum(1 << bit for bit in config.QA_CLOUD_BITS)
    clear = qa.bitwiseAnd(cloud_bits).eq(0)
    st_qa_ok = (
        image.select(config.ST_QA_BAND)
        .multiply(config.ST_QA_SCALE)
        .lte(config.ST_QA_MAX_K)
    )
    red = (
        image.select(config.NDVI_RED_BAND)
        .multiply(config.SR_SCALE)
        .add(config.SR_OFFSET)
    )
    nir = (
        image.select(config.NDVI_NIR_BAND)
        .multiply(config.SR_SCALE)
        .add(config.SR_OFFSET)
    )
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")
    swir1 = image.select("SR_B6").multiply(config.SR_SCALE).add(config.SR_OFFSET)
    ndbi = swir1.subtract(nir).divide(swir1.add(nir)).rename("ndbi")
    lst = (
        image.select(config.LST_BAND)
        .multiply(config.LST_SCALE)
        .add(config.LST_OFFSET)
        .rename("lst_k")
    )
    valid = clear.And(st_qa_ok).And(lst.mask()).And(ndvi.mask())
    return (
        lst.updateMask(valid)
        .addBands(ndvi.updateMask(valid))
        .addBands(ndbi.updateMask(valid))
        .addBands(valid.rename("valid"))
    )


def extract_landsat_raw(collection, x_min, y_max, cells):
    """Extract raw Landsat bands per scene, compute median in Python."""
    n = collection.size().getInfo()
    lst_stack = []
    ndvi_stack = []
    ndbi_stack = []
    n_obs_stack = []

    for i in range(n):
        img = ee.Image(collection.toList(n).get(i))
        result = compute_300_raw(img, ["ST_B10", "SR_B4", "SR_B5", "SR_B6", "QA_PIXEL", "ST_QA"], x_min, y_max)
        lst_raw = result["ST_B10"]
        sr_b4 = result["SR_B4"]
        sr_b5 = result["SR_B5"]
        sr_b6 = result["SR_B6"]
        qa = result["QA_PIXEL"]
        st_qa = result["ST_QA"]

        cloud_bits = sum(1 << bit for bit in config.QA_CLOUD_BITS)
        clear = (qa & cloud_bits) == 0
        st_qa_ok = (st_qa * config.ST_QA_SCALE) <= config.ST_QA_MAX_K

        lst = lst_raw * config.LST_SCALE + config.LST_OFFSET
        sr_b4_s = sr_b4 * config.SR_SCALE + config.SR_OFFSET
        sr_b5_s = sr_b5 * config.SR_SCALE + config.SR_OFFSET
        sr_b6_s = sr_b6 * config.SR_SCALE + config.SR_OFFSET
        ndvi = (sr_b5_s - sr_b4_s) / (sr_b5_s + sr_b4_s)
        ndbi = (sr_b6_s - sr_b5_s) / (sr_b6_s + sr_b5_s)
        sr_pos = (sr_b4_s > 0) & (sr_b5_s > 0) & (sr_b6_s > 0)

        lst = np.where(clear & st_qa_ok, lst, np.nan)
        ndvi = np.where(clear & st_qa_ok & sr_pos, ndvi, np.nan)
        ndbi = np.where(clear & st_qa_ok & sr_pos, ndbi, np.nan)

        lst_stack.append(lst)
        ndvi_stack.append(ndvi)
        ndbi_stack.append(ndbi)
        n_obs_stack.append(clear.astype(float))

    lst_stack = np.stack(lst_stack, axis=0)
    ndvi_stack = np.stack(ndvi_stack, axis=0)
    ndbi_stack = np.stack(ndbi_stack, axis=0)
    n_obs_stack = np.stack(n_obs_stack, axis=0)

    lst_median = np.nanmedian(lst_stack, axis=0)
    ndvi_median = np.nanmedian(ndvi_stack, axis=0)
    ndbi_median = np.nanmedian(ndbi_stack, axis=0)
    n_obs_sum = np.sum(n_obs_stack, axis=0)

    lst_values = lst_median[cells["row"], cells["col"]]
    ndvi_values = ndvi_median[cells["row"], cells["col"]]
    ndbi_values = ndbi_median[cells["row"], cells["col"]]
    n_obs_values = n_obs_sum[cells["row"], cells["col"]]

    return lst_values, ndvi_values, ndbi_values, n_obs_values


def extract_dynamic_world(region, years, x_min, y_max, cells):
    results = {}
    for year in years:
        collection = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(region)
            .filterDate(f"{year}-{config.SEASON_START}", f"{year}-{config.SEASON_END}")
            .select("built")
        )
        n = collection.size().getInfo()
        if n == 0:
            results[year] = np.full(len(cells), np.nan)
            continue
        mean_img = collection.mean()
        result = compute_300_raw(mean_img, ["built"], x_min, y_max)
        arr = np.where(result["built"] == -9999.0, np.nan, result["built"])
        results[year] = arr[cells["row"], cells["col"]]
    return results


def extract_worldcover(region, x_min, y_max, cells):
    wc_img = ee.ImageCollection("ESA/WorldCover/v200").first()
    built = wc_img.select("Map").eq(50).rename("built_frac")
    result = compute_300_raw(built, ["built_frac"], x_min, y_max)
    arr = np.where(result["built_frac"] == -9999.0, np.nan, result["built_frac"])
    return arr[cells["row"], cells["col"]]


def extract_metrics_for_city(city, refresh=False):
    output_path = Path("data") / city / METRICS_FILENAME
    if output_path.exists() and not refresh:
        print(f"{city}: {output_path} exists, skipping extraction (use --refresh to overwrite)")
        return pd.read_parquet(output_path)

    print(f"{city}: Initializing Earth Engine...")
    ee.Initialize(project=config.EE_PROJECT)
    print(f"{city}: Earth Engine initialized")

    grid_df = pd.read_parquet(Path("data") / city / "grid.parquet")
    ids = grid_df["grid_id"].str.split("_", expand=True).astype(int)
    grid_df["col"] = ids[0]
    grid_df["row"] = ids[1]
    cells = grid_df.loc[~grid_df["water"]].copy()
    print(f"{city}: Non-water cells: {len(cells)}")

    half_cell = config.GRID_CELL_SIZE_M / 2
    x_min = float(grid_df["x"].min()) - half_cell
    y_max = float(grid_df["y"].max()) + half_cell

    lat, lon = config.CITIES[city]
    region = ee.Geometry.Point([lon, lat]).buffer(config.RADIUS_KM * 1000)

    frames = []
    for year in config.YEARS:
        print(f"{city} {year}: Building Landsat collection...")
        collection = (
            ee.ImageCollection(config.LANDSAT_ASSETS[0])
            .merge(ee.ImageCollection(config.LANDSAT_ASSETS[1]))
            .filterBounds(region)
            .filterDate(
                f"{year}-{config.SEASON_START}",
                f"{year}-{config.SEASON_END}",
            )
        )
        n_scenes = collection.size().getInfo()
        print(f"{city} {year}: Found {n_scenes} scenes")
        if n_scenes == 0:
            raise SystemExit(f"{city} {year}: no Landsat scenes")

        print(f"{city} {year}: Extracting LST/NDVI/NDBI per-scene...")
        lst, ndvi, ndbi, n_obs = extract_landsat_raw(
            collection, x_min, y_max, cells
        )
        print(f"{city} {year}: Landsat extraction done")

        frames.append(
            pd.DataFrame(
                {
                    "grid_id": cells["grid_id"].to_numpy(),
                    "year": year,
                    "lst_k": lst,
                    "ndvi": ndvi,
                    "ndbi": ndbi,
                    "n_obs": n_obs,
                }
            )
        )
        print(
            f"{city} {year}: {n_scenes} scenes, "
            f"{int(np.isnan(lst).sum())} missing LST cells"
        )

    print(f"{city}: Extracting Dynamic World...")
    dw_results = {}
    for year in config.YEARS:
        collection = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(region)
            .filterDate(f"{year}-{config.SEASON_START}", f"{year}-{config.SEASON_END}")
            .select("built")
        )
        n = collection.size().getInfo()
        if n == 0:
            dw_results[year] = np.full(len(cells), np.nan)
            continue
        mean_img = collection.mean()
        result = compute_300_raw(mean_img, ["built"], x_min, y_max)
        arr = np.where(result["built"] == -9999.0, np.nan, result["built"])
        dw_results[year] = arr[cells["row"], cells["col"]]
    print(f"{city}: Dynamic World done")

    print(f"{city}: Extracting WorldCover...")
    wc_img = ee.ImageCollection("ESA/WorldCover/v200").first()
    built = wc_img.select("Map").eq(50).rename("built_frac")
    result = compute_300_raw(built, ["built_frac"], x_min, y_max)
    wc_values = np.where(result["built_frac"] == -9999.0, np.nan, result["built_frac"])
    wc_values = wc_values[cells["row"], cells["col"]]
    print(f"{city}: WorldCover done")

    output = pd.concat(frames, ignore_index=True)
    dw_all = np.concatenate([dw_results[y] for y in config.YEARS])
    output["dw_built"] = dw_all
    output["wc_built"] = np.tile(wc_values, len(config.YEARS))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(output_path, index=False)
    print(f"{city}: wrote {len(output)} rows to {output_path}")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-extraction from Earth Engine even if cached",
    )
    args = parser.parse_args()

    city = args.city
    extract_metrics_for_city(city, refresh=args.refresh)

    panel = pd.read_parquet(Path("data") / city / "panel.parquet")
    metrics = pd.read_parquet(Path("data") / city / METRICS_FILENAME)

    merged = panel.merge(
        metrics[["grid_id", "year", "ndbi", "dw_built", "wc_built"]],
        on=["grid_id", "year"],
        how="inner",
    )

    print(f"{city}: panel rows={len(panel)}, merged rows={len(merged)}")

    metric_cols = ["built", "ndbi", "dw_built", "wc_built", "ndvi", "lst_rel"]
    corr = merged[metric_cols].corr(method="spearman")

    print(f"\n{city}: Spearman correlation matrix:")
    print(corr.round(4).to_string())

    merged["bare_proxy"] = (merged["ndvi"] < merged["ndvi"].median()).astype(float)
    corr_bare = merged[["ndbi", "dw_built", "wc_built", "bare_proxy"]].corr(
        method="spearman"
    )["bare_proxy"]
    print(f"\n{city}: Spearman correlation with bare-soil proxy:")
    print(corr_bare.round(4).to_string())

    cell_ids = merged["grid_id"].unique()
    rng = np.random.default_rng(SEED)
    if len(cell_ids) > SUBSAMPLE_CELLS:
        sampled_cells = rng.choice(cell_ids, size=SUBSAMPLE_CELLS, replace=False)
        sub = merged[merged["grid_id"].isin(sampled_cells)].copy()
    else:
        sub = merged.copy()

    year_levels = sorted(int(year) for year in sub["year"].unique())
    sub["year_code"] = sub["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )

    splits = make_folds(sub, n_folds=config.CV_FOLDS)

    metrics_to_test = ["built", "ndbi", "dw_built", "wc_built"]
    results = {}

    for metric in metrics_to_test:
        X = sub[[metric, "ndvi", "year_code"]].to_numpy(dtype=float)
        y = sub["lst_rel"].to_numpy(dtype=float)
        valid = ~np.isnan(X).any(axis=1) & ~np.isnan(y)

        linear_terms = s(0, spline_order=1) + f(2)
        linear_gam = LinearGAM(linear_terms)
        linear_gam.gridsearch(X[valid], y[valid], lam=LAM_GRID, progress=False)
        linear_lam = flat_lam(linear_gam.lam)
        linear_scores = cv_scores(
            linear_terms, X, y, splits, linear_lam, valid
        )

        nonlinear_terms = s(0) + s(1) + te(0, 1) + f(2)
        nonlinear_gam = LinearGAM(nonlinear_terms)
        nonlinear_gam.gridsearch(X[valid], y[valid], lam=LAM_GRID, progress=False)
        nonlinear_lam = flat_lam(nonlinear_gam.lam)
        nonlinear_scores = cv_scores(
            nonlinear_terms, X, y, splits, nonlinear_lam, valid
        )

        fold_diffs = [nl - lin for nl, lin in zip(nonlinear_scores, linear_scores)]
        mean_gain = float(np.mean(fold_diffs))
        folds_favor = int(sum(1 for d in fold_diffs if d > 0))

        results[metric] = {
            "linear_cv_mean": float(np.mean(linear_scores)),
            "nonlinear_cv_mean": float(np.mean(nonlinear_scores)),
            "mean_gain": mean_gain,
            "folds_favor_nonlinear": folds_favor,
            "nl_selected_lam": nonlinear_lam,
            "lin_selected_lam": linear_lam,
            "nl_fold_scores": [float(s) for s in nonlinear_scores],
            "lin_fold_scores": [float(s) for s in linear_scores],
            "fold_differences": [float(d) for d in fold_diffs],
            "negligible_gain": bool(mean_gain < 0.005),
        }

        print(
            f"  {metric}: linear CV R2={np.mean(linear_scores):.4f}, "
            f"nonlinear CV R2={np.mean(nonlinear_scores):.4f}, "
            f"gain={mean_gain:.4f}"
        )

    city_median_ndvi = float(merged["ndvi"].median())
    year_2022_code = year_levels.index(2022) if 2022 in year_levels else 0

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    metric_labels = {
        "built": "GHS-BUILT-S",
        "ndbi": "Landsat NDBI",
        "dw_built": "Dynamic World",
        "wc_built": "ESA WorldCover",
    }

    for i, metric in enumerate(metrics_to_test):
        sub_m = sub[[metric, "ndvi", "year_code", "lst_rel"]].copy()
        q01, q99 = sub_m[metric].quantile([0.01, 0.99])
        eval_vals = np.linspace(q01, q99, 50)
        X_eval = np.column_stack(
            [eval_vals, np.full(50, city_median_ndvi), np.full(50, float(year_2022_code))]
        )
        X_m = sub_m[[metric, "ndvi", "year_code"]].to_numpy(dtype=float)
        y_m = sub_m["lst_rel"].to_numpy(dtype=float)
        valid_m = ~np.isnan(X_m).any(axis=1) & ~np.isnan(y_m)
        terms = s(0) + s(1) + te(0, 1) + f(2)
        gam = LinearGAM(terms)
        gam.gridsearch(X_m[valid_m], y_m[valid_m], lam=LAM_GRID, progress=False)
        pred = gam.predict(X_eval)
        ax.plot(eval_vals, pred, color=colors[i], label=metric_labels[metric], linewidth=1.5)

    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Built-up metric value")
    ax.set_ylabel("Total effect (K)")
    ax.set_title(
        f"{city}: built-up metric comparison\n"
        f"year 2022, NDVI={city_median_ndvi:.3f}"
    )
    ax.legend(loc="best")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(Path("outputs") / city / "fig6_rq2_metrics.png", dpi=150)
    plt.close(fig)

    csv_rows = []
    for metric in metrics_to_test:
        r = results[metric]
        csv_rows.append(
            {
                "metric": metric,
                "metric_label": metric_labels[metric],
                "linear_cv_mean": r["linear_cv_mean"],
                "nonlinear_cv_mean": r["nonlinear_cv_mean"],
                "mean_gain": r["mean_gain"],
                "folds_favor_nonlinear": r["folds_favor_nonlinear"],
                "nl_selected_lam": r["nl_selected_lam"],
                "lin_selected_lam": r["lin_selected_lam"],
                "negligible_gain": bool(r["mean_gain"] < 0.005),
            }
        )
    csv_df = pd.DataFrame(csv_rows)
    csv_df.to_csv(Path("outputs") / city / "rq2_metrics.csv", index=False)

    json_out = {
        "city": city,
        "subsample_cells": int(sub["grid_id"].nunique()),
        "subsample_rows": int(len(sub)),
        "n_folds": config.CV_FOLDS,
        "block_size_m": config.BLOCK_SIZE_M,
        "lam_grid": [float(v) for v in LAM_GRID],
        "city_median_ndvi": city_median_ndvi,
        "correlation_matrix": corr.round(6).to_dict(),
        "bare_soil_corr": corr_bare.round(6).to_dict(),
        "metrics": results,
    }
    with open(Path("outputs") / city / "rq2_metrics.json", "w") as h:
        json.dump(json_out, h, indent=2)

    print(f"{city}: wrote outputs/{city}/rq2_metrics.csv")
    print(f"{city}: wrote outputs/{city}/rq2_metrics.json")
    print(f"{city}: wrote outputs/{city}/fig6_rq2_metrics.png")


if __name__ == "__main__":
    main()
