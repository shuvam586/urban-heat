import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    grid = pd.read_parquet(Path("data") / args.city / "grid.parquet")
    panel = pd.read_parquet(Path("data") / args.city / "panel.parquet")

    required = {
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
    }
    missing = required - set(panel.columns)
    if missing:
        sys.exit(f"missing columns: {sorted(missing)}")

    water_ids = set(grid.loc[grid["water"], "grid_id"])
    remaining_water = set(panel["grid_id"]) & water_ids
    if remaining_water:
        sys.exit(f"{len(remaining_water)} water cells remain in the panel")

    for year in config.YEARS:
        sub = panel[panel["year"] == year]
        if sub.empty:
            sys.exit(f"{year}: no rows")

        rural = sub[sub["ladder_class"].isin(config.SMOD_RURAL)]
        if len(rural) < config.MIN_RURAL_CELLS:
            sys.exit(
                f"{year}: {len(rural)} rural cells, "
                f"below {config.MIN_RURAL_CELLS}"
            )

        median_rel = rural["lst_rel"].median()
        if abs(median_rel) > 1e-6:
            sys.exit(
                f"{year}: rural median lst_rel is {median_rel:.9f}, not 0"
            )

        print(
            f"{year}: rows={len(sub)}, rural={len(rural)}, "
            f"rural median lst_rel={median_rel:.9f}, "
            f"n_obs min={sub['n_obs'].min():.3f}"
        )

    counts = pd.crosstab(panel["ladder_class"], panel["year"])
    print("cell counts by class and year:")
    print(counts.to_string())
    print("OK")


if __name__ == "__main__":
    main()
