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

    path = Path("data") / args.city / "landsat.parquet"
    df = pd.read_parquet(path)

    required = {"grid_id", "year", "lst_k", "ndvi", "n_obs"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"missing columns: {sorted(missing)}")

    years = sorted(int(year) for year in df["year"].unique())
    if years != sorted(config.YEARS):
        sys.exit(f"years present {years}, expected {sorted(config.YEARS)}")

    if df["n_obs"].isna().any():
        sys.exit("n_obs has missing values")

    for year in config.YEARS:
        sub = df[df["year"] == year]
        if sub.empty:
            sys.exit(f"{year}: no rows")

        lst = sub["lst_k"].dropna()
        if lst.empty:
            sys.exit(f"{year}: no valid LST")

        if not lst.between(270, 340).all():
            sys.exit(
                f"{year}: LST outside 270-340 K "
                f"({lst.min():.3f} to {lst.max():.3f})"
            )

        missing_share = sub["lst_k"].isna().mean()
        if missing_share > config.MAX_MISSING_LST_SHARE:
            sys.exit(
                f"{year}: missing LST share {missing_share:.4f} exceeds "
                f"{config.MAX_MISSING_LST_SHARE}"
            )

        below_min = int((sub["n_obs"] < config.MIN_CLEAR_OBS).sum())
        print(
            f"{year}: rows={len(sub)}, "
            f"missing LST={missing_share:.4f}, "
            f"LST {lst.min():.3f}-{lst.max():.3f} K, "
            f"n_obs<{config.MIN_CLEAR_OBS}={below_min}"
        )

    print("OK")


if __name__ == "__main__":
    main()
