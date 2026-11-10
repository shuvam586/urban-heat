import argparse
from pathlib import Path

import pandas as pd

import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    grid = pd.read_parquet(Path("data") / city / "grid.parquet")
    landsat = pd.read_parquet(Path("data") / city / "landsat.parquet")

    landsat = landsat.loc[
        (landsat["n_obs"] >= config.MIN_CLEAR_OBS)
        & landsat["lst_k"].notna()
        & landsat["ndvi"].notna()
    ].copy()

    grid_columns = ["grid_id", "x", "y", "smod", "ladder_class", "built"]
    panel = landsat.merge(grid[grid_columns], on="grid_id", how="inner")

    parts = []
    for year in config.YEARS:
        sub = panel[panel["year"] == year].copy()
        rural = sub["ladder_class"].isin(config.SMOD_RURAL)
        n_rural = int(rural.sum())
        if n_rural < config.MIN_RURAL_CELLS:
            raise SystemExit(
                f"{city} {year}: only {n_rural} rural cells "
                f"(minimum {config.MIN_RURAL_CELLS})"
            )
        reference = sub.loc[rural, "lst_k"].median()
        sub["lst_rel"] = sub["lst_k"] - reference
        parts.append(sub)

    panel = pd.concat(parts, ignore_index=True)
    columns = [
        "grid_id",
        "year",
        "x",
        "y",
        "smod",
        "ladder_class",
        "built",
        "lst_k",
        "ndvi",
        "n_obs",
        "lst_rel",
    ]
    panel = panel[columns]

    path = Path("data") / city / "panel.parquet"
    panel.to_parquet(path, index=False)
    print(f"{city}: wrote {len(panel)} rows to {path}")

    for year in config.YEARS:
        sub = panel[panel["year"] == year]
        n_rural = int(sub["ladder_class"].isin(config.SMOD_RURAL).sum())
        print(f"{year}: {len(sub)} rows, {n_rural} rural cells")


if __name__ == "__main__":
    main()
