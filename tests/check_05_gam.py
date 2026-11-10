import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    output_dir = Path("outputs") / args.city
    with open(output_dir / "cv.json") as handle:
        cv = json.load(handle)

    required = {
        "model",
        "n_folds",
        "block_size_m",
        "r2_scores",
        "r2_mean",
        "r2_std",
        "converged",
        "subsample_cells",
        "subsample_rows",
        "model_comparisons",
        "built_total_min",
        "built_total_max",
        "built_total_shape_words",
        "built_unsupported_words",
        "n_cells_above_built_0.4",
        "n_cells_above_built_0.5",
        "fig3_bins",
        "fig3_min_count",
        "fig3_mask",
        "fig3_max_bin_count",
        "fig3_max_bin_masked",
    }
    missing = required - set(cv)
    if missing:
        sys.exit(f"missing cv.json keys: {sorted(missing)}")

    if cv["n_folds"] != config.CV_FOLDS:
        sys.exit(f"n_folds is {cv['n_folds']}, expected {config.CV_FOLDS}")
    if cv["block_size_m"] != config.BLOCK_SIZE_M:
        sys.exit("block size mismatch")
    if len(cv["r2_scores"]) != config.CV_FOLDS:
        sys.exit("held-out R2 scores do not match fold count")
    if not cv["converged"]:
        sys.exit("GAM did not converge")
    if not cv["subsample_cells"] or not cv["subsample_rows"]:
        sys.exit("invalid subsample size")

    comparisons = cv["model_comparisons"]
    if comparisons.get("scope") != "fixed part of step 05":
        sys.exit("model comparisons are not labelled as step 05")
    models = comparisons.get("models", {})
    for name in ("ndvi_year", "built_year", "full"):
        if name not in models:
            sys.exit(f"missing comparison model {name}")
        if len(models[name]["r2_scores"]) != config.CV_FOLDS:
            sys.exit(f"{name} does not have {config.CV_FOLDS} fold scores")
    if not np.allclose(
        models["full"]["r2_scores"], cv["r2_scores"]
    ):
        sys.exit("full-model comparison does not use the same folds")

    panel = pd.read_parquet(Path("data") / args.city / "panel.parquet")
    built_edges = np.linspace(
        panel["built"].min(),
        panel["built"].max(),
        cv["fig3_bins"] + 1,
    )
    ndvi_edges = np.linspace(
        panel["ndvi"].min(),
        panel["ndvi"].max(),
        cv["fig3_bins"] + 1,
    )
    counts, _, _ = np.histogram2d(
        panel["built"], panel["ndvi"], bins=[built_edges, ndvi_edges]
    )
    expected_mask = counts.T < cv["fig3_min_count"]
    saved_mask = np.array(cv["fig3_mask"], dtype=bool)
    if saved_mask.shape != expected_mask.shape:
        sys.exit("saved mask shape is wrong")
    if not np.array_equal(saved_mask, expected_mask):
        sys.exit("saved mask does not equal transposed-correct counts")
    wrong_mask = counts < cv["fig3_min_count"]
    if np.array_equal(saved_mask, wrong_mask):
        sys.exit("saved mask is the untransposed count table")

    max_i, max_j = np.unravel_index(np.argmax(counts), counts.shape)
    if saved_mask[max_j, max_i]:
        sys.exit("densest bin is masked")
    if cv["fig3_max_bin_masked"]:
        sys.exit("cv.json says the densest bin is masked")
    if cv["fig3_max_bin_count"] != int(counts.max()):
        sys.exit("cv.json max-bin count does not match panel")

    n_above_04 = int((panel["built"] > 0.4).sum())
    n_above_05 = int((panel["built"] > 0.5).sum())
    if cv["n_cells_above_built_0.4"] != n_above_04:
        sys.exit("built > 0.4 count does not match panel")
    if cv["n_cells_above_built_0.5"] != n_above_05:
        sys.exit("built > 0.5 count does not match panel")
    if "non-monotonic" in cv["built_total_shape_words"].lower():
        sys.exit("shape words still use the removed label")
    if "unsupported" not in cv["built_unsupported_words"].lower():
        sys.exit("unsupported/sparse statement is missing")
    if not np.isfinite(cv["built_total_min"]) or not np.isfinite(
        cv["built_total_max"]
    ):
        sys.exit("total built effect range is not finite")

    for figure in ("fig2_builtup.png", "fig3_interaction.png"):
        if not (output_dir / figure).exists():
            sys.exit(f"{figure} missing")

    print("model comparisons (fixed part of step 05, same 5 km folds):")
    for name in ("ndvi_year", "built_year", "full"):
        model = models[name]
        print(
            f"  {name}: mean {model['r2_mean']:.6f}, "
            f"spread {model['r2_std']:.6f}, "
            f"lam {model['selected_lam']}, "
            f"scores {[round(value, 6) for value in model['r2_scores']]}"
        )
    print(
        f"fig3 mask: {cv['fig3_bins']}x{cv['fig3_bins']} bins, "
        f"max bin {cv['fig3_max_bin_count']} cells, "
        f"masked={cv['fig3_max_bin_masked']}; "
        "saved mask equals transposed-correct counts"
    )
    print(
        f"total built effect: {cv['built_total_min']:.3f} to "
        f"{cv['built_total_max']:.3f} K"
    )
    print(
        f"cells above built 0.4={cv['n_cells_above_built_0.4']:,}, "
        f"above 0.5={cv['n_cells_above_built_0.5']:,}"
    )
    print("OK")


if __name__ == "__main__":
    main()
