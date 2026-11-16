import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
REFERENCES = ["Ref_A", "Ref_B", "Ref_C"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    output_dir = Path("outputs") / args.city
    csv_path = output_dir / "rq1_references.csv"
    rq1 = pd.read_csv(csv_path)

    required = {
        "year",
        "reference",
        "class",
        "median",
        "ci_low",
        "ci_high",
        "n_cells",
        "ref_n_cells",
        "ref_n_blocks",
    }
    missing = required - set(rq1.columns)
    if missing:
        sys.exit(f"missing columns: {sorted(missing)}")

    years = sorted(int(year) for year in rq1["year"].unique())
    if years != sorted(config.YEARS):
        sys.exit(f"years present {years}, expected {sorted(config.YEARS)}")

    if sorted(rq1["reference"].unique()) != sorted(REFERENCES):
        sys.exit(f"references present {sorted(rq1['reference'].unique())}")

    for year in config.YEARS:
        sub = rq1[rq1["year"] == year]
        if sorted(sub["class"].unique()) != sorted(CLASS_ORDER):
            sys.exit(f"{year}: classes present {sorted(sub['class'].unique())}")

    if rq1[["median", "ci_low", "ci_high"]].isna().any().any():
        sys.exit("non-finite median or interval")

    if not (rq1["ci_low"] <= rq1["median"]).all():
        sys.exit("ci_low exceeds median")

    if not (rq1["median"] <= rq1["ci_high"]).all():
        sys.exit("median exceeds ci_high")

    if not (rq1["n_cells"] > 0).all():
        sys.exit("empty class")

    if not (rq1["ref_n_cells"] >= 200).all():
        sys.exit("reference group below 200 cells")

    if not (rq1["ref_n_blocks"] >= 30).all():
        sys.exit("reference group below 30 distinct 5 km blocks")

    # Ref_A point medians must match gradient.csv within 1e-6 K (baseline check)
    gradient = pd.read_csv(output_dir / "gradient.csv")
    ref_a = rq1[rq1["reference"] == "Ref_A"]
    merged = ref_a.merge(
        gradient[["year", "class", "median"]],
        on=["year", "class"],
        suffixes=("_rq1", "_grad"),
    )
    if len(merged) != len(config.YEARS) * len(CLASS_ORDER):
        sys.exit("Ref_A rows do not cover all year/class combinations")
    if not (abs(merged["median_rq1"] - merged["median_grad"]) <= 1e-6).all():
        worst = (abs(merged["median_rq1"] - merged["median_grad"])).max()
        sys.exit(f"Ref_A medians do not match gradient.csv within 1e-6 K (worst {worst:.3e})")

    if not (output_dir / "fig4_rq1_references.png").exists():
        sys.exit("fig4_rq1_references.png missing")

    print(rq1.to_string(index=False))
    print("OK")


if __name__ == "__main__":
    main()
