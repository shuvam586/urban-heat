import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    output_dir = Path("outputs") / args.city
    json_path = output_dir / "rq2_context.json"
    csv_path = output_dir / "rq2_context.csv"
    fig_path = output_dir / "fig5_rq2_context.png"

    if not json_path.exists():
        sys.exit(f"{json_path} missing")
    if not csv_path.exists():
        sys.exit(f"{csv_path} missing")
    if not fig_path.exists():
        sys.exit(f"{fig_path} missing")

    with open(json_path) as handle:
        result = json.load(handle)

    required_top = {
        "city",
        "subsample_cells",
        "subsample_rows",
        "n_folds",
        "block_size_m",
        "lam_grid",
        "n_bootstrap",
        "bootstrap_seed",
        "city_median_ndvi",
        "coverage",
        "context_results",
        "part_b",
    }
    missing = required_top - set(result.keys())
    if missing:
        sys.exit(f"missing top-level keys: {sorted(missing)}")

    if result["city"] != args.city:
        sys.exit(f"city is {result['city']}, expected {args.city}")
    if result["n_folds"] != config.CV_FOLDS:
        sys.exit(f"n_folds is {result['n_folds']}, expected {config.CV_FOLDS}")
    if result["block_size_m"] != config.BLOCK_SIZE_M:
        sys.exit("block size mismatch")

    # --- Fold alignment with cv.json ---
    cv_path = output_dir / "cv.json"
    if not cv_path.exists():
        sys.exit("cv.json missing; cannot verify fold alignment")
    with open(cv_path) as handle:
        cv = json.load(handle)
    if result["subsample_cells"] != cv["subsample_cells"]:
        sys.exit(
            f"subsample_cells {result['subsample_cells']} != cv.json "
            f"{cv['subsample_cells']}"
        )
    if result["subsample_rows"] != cv["subsample_rows"]:
        sys.exit(
            f"subsample_rows {result['subsample_rows']} != cv.json "
            f"{cv['subsample_rows']}"
        )

    # --- Coverage checks ---
    for cov in result["coverage"]:
        if not isinstance(cov["eligible"], bool):
            sys.exit(f"coverage {cov['context']}: eligible not boolean")
        if cov["eligible"]:
            if cov["n_cells"] < 500:
                sys.exit(
                    f"coverage {cov['context']}: eligible but n_cells={cov['n_cells']} < 500"
                )
            if cov["n_blocks"] < 30:
                sys.exit(
                    f"coverage {cov['context']}: eligible but n_blocks={cov['n_blocks']} < 30"
                )
        if not (0.0 <= cov["built_q05"] <= cov["built_q099"] <= 1.0):
            sys.exit(
                f"coverage {cov['context']}: built quantiles out of range"
            )

    # --- Context results checks ---
    contexts_seen = set()
    for cr in result["context_results"]:
        if cr["context"] in contexts_seen:
            sys.exit(f"duplicate context {cr['context']}")
        contexts_seen.add(cr["context"])
        allowed_cr = {
            "context",
            "eligible",
            "n_cells",
            "n_blocks",
            "built_q01",
            "built_q099",
            "median_ndvi",
            "selected_lam",
            "n_cells_subsampled",
            "n_rows_subsampled",
            "reason",
        }
        if set(cr.keys()) - allowed_cr:
            sys.exit(f"context {cr['context']}: unexpected keys")
        if cr["eligible"]:
            for key in ("n_cells", "n_blocks", "built_q01", "built_q099", "selected_lam"):
                if key not in cr or cr[key] is None:
                    sys.exit(f"context {cr['context']}: eligible but missing {key}")
            if cr["n_cells"] < 500 or cr["n_blocks"] < 30:
                sys.exit(
                    f"context {cr['context']}: eligible but below threshold"
                )
        else:
            if "reason" not in cr or not cr["reason"]:
                sys.exit(f"context {cr['context']}: not eligible but no reason")

    # --- CSV checks ---
    csv = pd.read_csv(csv_path)
    required_csv = {"context", "eligible", "built", "pred", "ci_low", "ci_high"}
    missing_csv = required_csv - set(csv.columns)
    if missing_csv:
        sys.exit(f"csv missing columns: {sorted(missing_csv)}")
    if csv["eligible"].notna().all() and csv["eligible"].dtype == bool:
        pass
    elif not (
        csv["eligible"].isin([True, False, 1, 0, "True", "False"]).all()
    ):
        sys.exit("csv eligible column has non-boolean values")

    eligible_csv = csv[csv["eligible"].isin([True, 1, "True"])]
    for label in CLASS_ORDER:
        sub_csv = eligible_csv[eligible_csv["context"] == label]
        cr = next((c for c in result["context_results"] if c["context"] == label), None)
        if cr is None or not cr["eligible"]:
            if len(sub_csv) > 0:
                sys.exit(f"{label}: not eligible but has CSV rows")
        else:
            if len(sub_csv) == 0:
                sys.exit(f"{label}: eligible but no CSV rows")
            # Check no extrapolation beyond built_q01/q099
            if sub_csv["built"].min() < cr["built_q01"] - 1e-9:
                sys.exit(
                    f"{label}: CSV built min {sub_csv['built'].min():.6f} < q01 {cr['built_q01']:.6f}"
                )
            if sub_csv["built"].max() > cr["built_q099"] + 1e-9:
                sys.exit(
                    f"{label}: CSV built max {sub_csv['built'].max():.6f} > q099 {cr['built_q099']:.6f}"
                )
            # Check CI ordering
            bad = sub_csv[
                (sub_csv["ci_low"] > sub_csv["pred"])
                | (sub_csv["pred"] > sub_csv["ci_high"])
            ]
            if len(bad) > 0:
                sys.exit(f"{label}: CI ordering violated in {len(bad)} rows")
            if not np.all(np.isfinite(sub_csv["pred"])):
                sys.exit(f"{label}: non-finite predictions")
            if not np.all(np.isfinite(sub_csv["ci_low"])) or not np.all(
                np.isfinite(sub_csv["ci_high"])
            ):
                sys.exit(f"{label}: non-finite CI values")

    # --- Part B checks ---
    pb = result["part_b"]
    required_pb = {
        "model_nonlinear",
        "model_linear",
        "nl_selected_lam",
        "lin_selected_lam",
        "nl_fold_scores",
        "lin_fold_scores",
        "fold_differences",
        "mean_gain",
        "folds_favour_nonlinear",
        "negligible_gain",
        "derivative_zero_crossings",
    }
    missing_pb = required_pb - set(pb.keys())
    if missing_pb:
        sys.exit(f"part_b missing keys: {sorted(missing_pb)}")

    if len(pb["nl_fold_scores"]) != config.CV_FOLDS:
        sys.exit("nonlinear fold scores != 5")
    if len(pb["lin_fold_scores"]) != config.CV_FOLDS:
        sys.exit("linear fold scores != 5")
    if len(pb["fold_differences"]) != config.CV_FOLDS:
        sys.exit("fold differences != 5")

    for score in pb["nl_fold_scores"] + pb["lin_fold_scores"]:
        if not np.isfinite(score):
            sys.exit("non-finite CV R2 score")

    expected_diffs = [
        nl - lin for nl, lin in zip(pb["nl_fold_scores"], pb["lin_fold_scores"])
    ]
    for saved, expected in zip(pb["fold_differences"], expected_diffs):
        if abs(saved - expected) > 1e-12:
            sys.exit("fold_differences do not match nl - lin scores")

    expected_mean = float(np.mean(pb["fold_differences"]))
    if abs(pb["mean_gain"] - expected_mean) > 1e-12:
        sys.exit("mean_gain does not match mean of fold_differences")

    expected_favours = int(sum(1 for d in pb["fold_differences"] if d > 0))
    if pb["folds_favour_nonlinear"] != expected_favours:
        sys.exit("folds_favour_nonlinear does not match fold_differences")

    expected_negligible = bool(expected_mean < 0.005)
    if pb["negligible_gain"] != expected_negligible:
        sys.exit("negligible_gain does not match mean_gain < 0.005")

    for crossing in pb["derivative_zero_crossings"]:
        if "type" not in crossing or "built" not in crossing:
            sys.exit("zero crossing missing type or built")
        if crossing["type"] not in ("min", "max"):
            sys.exit(f"zero crossing type {crossing['type']} not min/max")
        if not (0.0 <= crossing["built"] <= 1.0):
            sys.exit("zero crossing built out of [0,1]")

    print(f"{args.city}: rq2_context.json valid")
    print(f"  subsample: {result['subsample_cells']} cells, {result['subsample_rows']} rows")
    print(f"  fold alignment with cv.json: OK (subsample_cells={result['subsample_cells']})")
    print("  Part A coverage:")
    for cov in result["coverage"]:
        print(
            f"    {cov['context']}: cells={cov['n_cells']}, blocks={cov['n_blocks']}, "
            f"eligible={cov['eligible']}"
        )
    print("  Part B:")
    print(
        f"    nonlinear lam={pb['nl_selected_lam']}, linear lam={pb['lin_selected_lam']}"
    )
    print(
        f"    mean gain={pb['mean_gain']:.6f}, "
        f"folds favour nonlinear={pb['folds_favour_nonlinear']}/5, "
        f"negligible={pb['negligible_gain']}"
    )
    print(f"    zero crossings: {pb['derivative_zero_crossings']}")
    print("OK")


if __name__ == "__main__":
    main()
