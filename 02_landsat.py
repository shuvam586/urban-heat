import argparse
from pathlib import Path

import ee
import numpy as np
import pandas as pd

import config

LST_FILL = -9999.0
TILE_SIZE = 167


def prep(image):
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
        .addBands(valid.rename("valid"))
    )


def compute_300(image, bands, x_min, y_max, fill):
    processed = (
        image.reduceResolution(ee.Reducer.mean(), maxPixels=1024)
        .reproject(
            crs=config.GRID_CRS,
            crsTransform=[
                config.GRID_CELL_SIZE_M,
                0,
                x_min,
                0,
                -config.GRID_CELL_SIZE_M,
                y_max,
            ],
        )
        .unmask(fill)
    )

    size = config.GRID_CELLS_PER_SIDE
    result = {
        band: np.full((size, size), fill, dtype=float) for band in bands
    }
    for row_start in range(0, size, TILE_SIZE):
        for col_start in range(0, size, TILE_SIZE):
            width = min(TILE_SIZE, size - col_start)
            height = min(TILE_SIZE, size - row_start)
            tile_grid = {
                "dimensions": {"width": width, "height": height},
                "affineTransform": {
                    "scaleX": config.GRID_CELL_SIZE_M,
                    "shearX": 0,
                    "translateX": x_min + col_start * config.GRID_CELL_SIZE_M,
                    "shearY": 0,
                    "scaleY": -config.GRID_CELL_SIZE_M,
                    "translateY": y_max - row_start * config.GRID_CELL_SIZE_M,
                },
                "crsCode": config.GRID_CRS,
            }
            pixels = ee.data.computePixels(
                {
                    "expression": processed,
                    "fileFormat": "NUMPY_NDARRAY",
                    "bandIds": bands,
                    "grid": tile_grid,
                }
            )
            for band in bands:
                result[band][
                    row_start : row_start + height,
                    col_start : col_start + width,
                ] = pixels[band]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    ee.Initialize(project=config.EE_PROJECT)
    grid_df = pd.read_parquet(Path("data") / city / "grid.parquet")

    ids = grid_df["grid_id"].str.split("_", expand=True).astype(int)
    grid_df["col"] = ids[0]
    grid_df["row"] = ids[1]
    cells = grid_df.loc[~grid_df["water"]].copy()

    half_cell = config.GRID_CELL_SIZE_M / 2
    x_min = grid_df["x"].min() - half_cell
    y_max = grid_df["y"].max() + half_cell

    lat, lon = config.CITIES[city]
    region = ee.Geometry.Point([lon, lat]).buffer(config.RADIUS_KM * 1000)

    frames = []
    for year in config.YEARS:
        collection = (
            ee.ImageCollection(config.LANDSAT_ASSETS[0])
            .merge(ee.ImageCollection(config.LANDSAT_ASSETS[1]))
            .filterBounds(region)
            .filterDate(
                f"{year}-{config.SEASON_START}",
                f"{year}-{config.SEASON_END}",
            )
            .map(prep)
        )
        n_scenes = collection.size().getInfo()
        if n_scenes == 0:
            raise SystemExit(f"{city} {year}: no Landsat scenes")

        projection = collection.first().select("lst_k").projection()
        combined = (
            collection.select(["lst_k", "ndvi"])
            .median()
            .setDefaultProjection(projection)
        )
        n_obs_image = (
            collection.select("valid")
            .sum()
            .rename("n_obs")
            .setDefaultProjection(projection)
        )

        bands = compute_300(
            combined, ["lst_k", "ndvi"], x_min, y_max, LST_FILL
        )
        n_obs = compute_300(
            n_obs_image, ["n_obs"], x_min, y_max, 0
        )["n_obs"]

        lst = np.where(bands["lst_k"] == LST_FILL, np.nan, bands["lst_k"])
        ndvi = np.where(bands["ndvi"] == LST_FILL, np.nan, bands["ndvi"])

        lst_values = lst[cells["row"], cells["col"]]
        ndvi_values = ndvi[cells["row"], cells["col"]]
        n_obs_values = n_obs[cells["row"], cells["col"]]

        frames.append(
            pd.DataFrame(
                {
                    "grid_id": cells["grid_id"].to_numpy(),
                    "year": year,
                    "lst_k": lst_values,
                    "ndvi": ndvi_values,
                    "n_obs": n_obs_values,
                }
            )
        )
        print(
            f"{year}: {n_scenes} scenes, "
            f"{int(np.isnan(lst_values).sum())} missing LST cells"
        )

    output = pd.concat(frames, ignore_index=True)
    path = Path("data") / city / "landsat.parquet"
    output.to_parquet(path, index=False)
    print(f"{city}: wrote {len(output)} rows to {path}")


if __name__ == "__main__":
    main()
