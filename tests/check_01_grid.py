import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    path = Path("data") / args.city / "grid.parquet"
    df = pd.read_parquet(path)

    required = {"grid_id", "x", "y", "smod", "ladder_class", "built", "water"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"missing columns: {sorted(missing)}")

    if not df["grid_id"].is_unique:
        sys.exit("grid_id is not unique")

    valid_smod = {config.SMOD_WATER, *config.SMOD_LADDER}
    bad_smod = sorted(set(df["smod"].dropna().unique()) - valid_smod)
    if bad_smod:
        sys.exit(f"unexpected smod codes: {bad_smod}")

    ladder_classes = set(config.SMOD_LADDER)
    invalid_non_water = df.loc[
        ~df["water"] & ~df["ladder_class"].isin(ladder_classes)
    ]
    if len(invalid_non_water):
        sys.exit(f"{len(invalid_non_water)} non-water cells have no ladder class")

    invalid_water = df.loc[
        df["water"]
        & df["ladder_class"].notna()
        & ~df["ladder_class"].isin(ladder_classes)
    ]
    if len(invalid_water):
        sys.exit("water cells have invalid ladder classes")

    if df["built"].isna().any():
        sys.exit("built has missing values")
    if not df["built"].between(0, 1).all():
        sys.exit("built outside 0 to 1")

    expected = (
        math.pi
        * (config.RADIUS_KM * 1000) ** 2
        / (config.GRID_CELL_SIZE_M**2)
    )
    if not (0.95 * expected <= len(df) <= 1.05 * expected):
        sys.exit(f"cell count {len(df)} is not about {expected:.0f}")

    print(f"cells: {len(df)} (expected about {expected:.0f})")
    print(f"grid_id unique: {df['grid_id'].is_unique}")
    print(f"built range: {df['built'].min():.6f} to {df['built'].max():.6f}")
    print(f"water cells: {int(df['water'].sum())}")
    print("cells by ladder class:")
    for code, count in df["ladder_class"].value_counts().sort_index().items():
        print(f"  {code}: {count}")
    print("OK")


if __name__ == "__main__":
    main()
