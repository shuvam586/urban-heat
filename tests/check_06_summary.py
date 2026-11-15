import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config


def direction_from_cv(cv):
    text = cv["built_total_shape_words"]
    match = re.search(
        r"from (-?\d+\.\d+)-(-?\d+\.\d+) K at built ([-\d.]+).*?"
        r"to (-?\d+\.\d+)-(-?\d+\.\d+) K at built ([-\d.]+)",
        text,
    )
    if match is None:
        sys.exit(f"cannot parse curve endpoints from cv.json: {text}")
    values = [float(value) for value in match.groups()]
    start_min, start_max, _, end_min, end_max, _ = values
    start_mid = 0.5 * (start_min + start_max)
    end_mid = 0.5 * (end_min + end_max)
    delta = end_mid - start_mid
    span = cv["built_total_max"] - cv["built_total_min"]
    if abs(delta) < 0.2:
        return "roughly flat"
    if span > 1.5 * abs(delta) + 0.2:
        return "non-monotonic"
    return "rises" if delta > 0 else "falls"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    output_dir = Path("outputs") / args.city
    path = output_dir / "summary.md"
    if not path.exists():
        sys.exit("summary.md missing")

    with open(output_dir / "cv.json") as handle:
        cv = json.load(handle)
    panel = pd.read_parquet(Path("data") / args.city / "panel.parquet")

    text = path.read_text(encoding="utf-8")
    lower = text.lower()

    required = [
        "total built effect",
        "s(built) + te",
        "95%",
        "model comparisons",
        "ndvi + year",
        "built + year",
        "full model",
        "zero-inflated",
        "below 0.1",
        "above 0.4",
        "h2",
        "unsupported",
        "class 23",
        "vegetation modification",
        "rule:",
        "done:",
        "shows:",
        "could be wrong:",
    ]
    missing = [item for item in required if item.lower() not in lower]
    if missing:
        sys.exit(f"summary.md missing: {missing}")

    dense_counts = panel[panel["ladder_class"] == 23].groupby("year").size()
    for year in config.YEARS:
        if year not in dense_counts.index:
            sys.exit(f"panel has no class 23 cells for {year}")
        token = f"{int(dense_counts.loc[year]):,}"
        if token not in text:
            sys.exit(
                f"summary.md missing class 23 count for {year}: {token}"
            )

    n04 = int((panel["built"] > 0.4).sum())
    n05 = int((panel["built"] > 0.5).sum())
    for label, value in (("above 0.4", n04), ("above 0.5", n05)):
        token = f"{value:,}"
        if token not in text:
            sys.exit(f"summary.md missing {label} cell count: {token}")

    direction = direction_from_cv(cv)
    if direction in ("non-monotonic", "roughly flat"):
        expected_phrase = f"the fitted total effect is {direction}"
    else:
        expected_phrase = f"the fitted total effect {direction}"
    if expected_phrase.lower() not in lower:
        sys.exit(
            "summary.md curve direction does not match cv.json: "
            f"expected '{direction}'"
        )

    for name in (
        "gradient.csv",
        "cv.json",
        "fig1_gradient.png",
        "fig2_builtup.png",
        "fig3_interaction.png",
    ):
        if not (output_dir / name).exists():
            sys.exit(f"{name} missing")

    print(f"summary.md: {path}")
    print(
        "verified: total-effect Fig 2, model comparisons, zero-inflation, "
        "H2, sparse support, class 23 counts, above-0.4 count, curve direction"
    )
    print("OK")


if __name__ == "__main__":
    main()
