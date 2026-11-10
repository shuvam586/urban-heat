import argparse

import ee

import config


def read_first(image, point, band, scale):
    value = (
        image.select(band)
        .reduceRegion(ee.Reducer.first(), point, scale=scale, maxPixels=1)
        .getInfo()
    )
    return value[band]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Hyderabad", choices=sorted(config.CITIES))
    args = parser.parse_args()

    ee.Initialize(project=config.EE_PROJECT)

    lat, lon = config.CITIES[args.city]
    point = ee.Geometry.Point([lon, lat])

    smod = ee.Image(f"{config.SMOD_ASSET}/{config.SMOD_EPOCH}")
    smod_value = read_first(smod, point, config.SMOD_BAND, 1000)

    year = config.YEARS[0]
    landsat = (
        ee.ImageCollection(config.LANDSAT_ASSETS[0])
        .filterBounds(point)
        .filterDate(f"{year}-{config.SEASON_START}", f"{year}-{config.SEASON_END}")
        .sort("CLOUD_COVER")
        .first()
    )
    lst = (
        landsat.select(config.LST_BAND)
        .multiply(config.LST_SCALE)
        .add(config.LST_OFFSET)
    )
    lst_value = read_first(lst, point, config.LST_BAND, 30)

    print(f"SMOD {config.SMOD_BAND}: {smod_value}")
    print(f"Landsat {config.LST_BAND} (K): {lst_value}")
    print("OK")


if __name__ == "__main__":
    main()
