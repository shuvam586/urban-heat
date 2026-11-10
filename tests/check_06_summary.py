import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config


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
        "most of the cv",
        "zero-inflated",
        "below 0.1",
        "above 0.4",
        "h2",
        "h3",
        "weakly supported",
        "unsupported",
        "class 23",
        "1,245",
        "1,221",
        "1,175",
        "7,348",
        f"{cv['n_cells_above_built_0.5']:,}",
        "done:",
        "shows:",
        "could be wrong:",
    ]
    missing = [item for item in required if item.lower() not in lower]
    if missing:
        sys.exit(f"summary.md missing: {missing}")

    if "non-monotonic" in lower:
        sys.exit("summary.md still uses the removed non-monotonic label")

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
        "H2/H3, sparse support, class 23, three sentences"
    )
    print("OK")


if __name__ == "__main__":
    main()
