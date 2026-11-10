import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
CLASS_MAP = {11: 0, 12: 0, 13: 0, 21: 1, 22: 2, 23: 3, 30: 4}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    output_dir = Path("outputs") / args.city
    gradient = pd.read_csv(output_dir / "gradient.csv")

    required = {"year", "class", "median", "ci_low", "ci_high", "n_cells"}
    missing = required - set(gradient.columns)
    if missing:
        sys.exit(f"missing columns: {sorted(missing)}")

    years = sorted(int(year) for year in gradient["year"].unique())
    if years != sorted(config.YEARS):
        sys.exit(f"years present {years}, expected {sorted(config.YEARS)}")

    for year in config.YEARS:
        sub = gradient[gradient["year"] == year]
        present = list(sub["class"])
        if sorted(present) != sorted(CLASS_ORDER):
            sys.exit(f"{year}: classes present {present}")

    if gradient[["median", "ci_low", "ci_high"]].isna().any().any():
        sys.exit("non-finite median or interval")

    if not (gradient["ci_low"] <= gradient["median"]).all():
        sys.exit("ci_low exceeds median")

    if not (gradient["median"] <= gradient["ci_high"]).all():
        sys.exit("median exceeds ci_high")

    if not (gradient["n_cells"] > 0).all():
        sys.exit("empty class")

    panel = pd.read_parquet(Path("data") / args.city / "panel.parquet")
    panel["class_group"] = panel["ladder_class"].map(CLASS_MAP)
    counts = (
        panel.groupby(["year", "class_group"])
        .size()
        .rename("panel_n")
        .reset_index()
    )
    counts["class"] = counts["class_group"].map(
        dict(enumerate(CLASS_ORDER))
    )
    merged = gradient.merge(
        counts[["year", "class", "panel_n"]],
        on=["year", "class"],
        how="left",
    )
    if not (merged["n_cells"] == merged["panel_n"]).all():
        sys.exit("gradient.csv cell counts do not match panel")

    if not (output_dir / "fig1_gradient.png").exists():
        sys.exit("fig1_gradient.png missing")

    print(gradient.to_string(index=False))
    print("OK")


if __name__ == "__main__":
    main()
