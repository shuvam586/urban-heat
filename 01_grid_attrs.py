import argparse
from pathlib import Path

import ee
import numpy as np
import pandas as pd

import config


def compute_layer(image, band, grid):
    pixels = ee.data.computePixels(
        {
            "expression": image,
            "fileFormat": "NUMPY_NDARRAY",
            "bandIds": [band],
            "grid": grid,
        }
    )
    return pixels[band]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    lat, lon = config.CITIES[city]

    ee.Initialize(project=config.EE_PROJECT)

    centre = ee.Geometry.Point([lon, lat]).transform(config.GRID_CRS)
    x0, y0 = centre.coordinates().getInfo()

    half = config.GRID_CELLS_PER_SIDE * config.GRID_CELL_SIZE_M / 2
    x_min = x0 - half
    y_max = y0 + half

    grid = {
        "dimensions": {
            "width": config.GRID_CELLS_PER_SIDE,
            "height": config.GRID_CELLS_PER_SIDE,
        },
        "affineTransform": {
            "scaleX": config.GRID_CELL_SIZE_M,
            "shearX": 0,
            "translateX": x_min,
            "shearY": 0,
            "scaleY": -config.GRID_CELL_SIZE_M,
            "translateY": y_max,
        },
        "crsCode": config.GRID_CRS,
    }

    smod_image = ee.Image(
        f"{config.SMOD_ASSET}/{config.SMOD_EPOCH}"
    ).select(config.SMOD_BAND)
    smod = compute_layer(smod_image, config.SMOD_BAND, grid)

    built_image = (
        ee.Image(f"{config.BUILT_ASSET}/{config.BUILT_EPOCH}")
        .select(config.BUILT_BAND)
        .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
    )
    built_m2 = compute_layer(built_image, config.BUILT_BAND, grid)

    water_image = (
        ee.Image(config.WATER_ASSET)
        .select(config.WATER_BAND)
        .unmask(0)
        .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
    )
    occurrence = compute_layer(water_image, config.WATER_BAND, grid)

    rows, cols = np.indices(smod.shape)
    x = x_min + (cols + 0.5) * config.GRID_CELL_SIZE_M
    y = y_max - (rows + 0.5) * config.GRID_CELL_SIZE_M
    keep = np.hypot(x - x0, y - y0) <= config.RADIUS_KM * 1000

    smod_kept = smod[keep].astype(int)
    water = (smod_kept == config.SMOD_WATER) | (
        occurrence[keep] > config.WATER_OCCURRENCE_THRESHOLD
    )
    ladder = np.where(
        np.isin(smod_kept, config.SMOD_LADDER) & ~water,
        smod_kept,
        0,
    )

    output = pd.DataFrame(
        {
            "grid_id": [
                f"{col}_{row}" for col, row in zip(cols[keep], rows[keep])
            ],
            "x": x[keep],
            "y": y[keep],
            "smod": smod_kept,
            "ladder_class": pd.array(
                [int(code) if code else None for code in ladder], dtype="Int16"
            ),
            "built": built_m2[keep] / config.BUILT_MAX_M2,
            "water": water,
        }
    )

    path = Path("data") / city / "grid.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(path, index=False)
    print(f"{city}: wrote {len(output)} cells to {path}")


if __name__ == "__main__":
    main()
