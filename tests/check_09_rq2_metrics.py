import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config

METRICS = ["built", "ndbi", "dw_built", "wc_built"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    output_dir = Path("outputs") / city
    data_dir = Path("data") / city

    json_path = output_dir / "rq2_metrics.json"
    csv_path = output_dir / "rq2_metrics.csv"
    fig_path = output_dir / "fig6_rq2_metrics.png"
    metrics_path = data_dir / "metrics.parquet"
    panel_path = data_dir / "panel.parquet"
    cv_path = output_dir / "cv.json"

    for p in [json_path, csv_path, fig_path, metrics_path, panel_path, cv_path]:
        if not p.exists():
            sys.exit(f"{p} missing")

    with open(json_path) as handle:
        result = json.load(handle)
    with open(cv_path) as handle:
        cv = json.load(handle)

    required_top = {
        "city",
        "subsample_cells",
        "subsample_rows",
        "n_folds",
        "block_size_m",
        "lam_grid",
        "city_median_ndvi",
        "correlation_matrix",
        "bare_soil_corr",
        "metrics",
    }
    missing = required_top - set(result.keys())
    if missing:
        sys.exit(f"missing top-level keys: {sorted(missing)}")

    if result["city"] != city:
        sys.exit(f"city is {result['city']}, expected {city}")
    if result["n_folds"] != config.CV_FOLDS:
        sys.exit(f"n_folds is {result['n_folds']}, expected {config.CV_FOLDS}")
    if result["block_size_m"] != config.BLOCK_SIZE_M:
        sys.exit("block size mismatch")

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

    metrics_df = pd.read_parquet(metrics_path)
    panel = pd.read_parquet(panel_path)

    panel_keys = set(zip(panel["grid_id"], panel["year"]))
    metrics_keys = set(zip(metrics_df["grid_id"], metrics_df["year"]))
    if not panel_keys <= metrics_keys:
        missing = panel_keys - metrics_keys
        sys.exit(
            f"metrics missing {len(missing)} panel grid/year combos, "
            f"e.g. {sorted(missing)[:5]}"
        )

    if not (
        (metrics_df["dw_built"] >= 0).all() and (metrics_df["dw_built"] <= 1).all()
    ):
        sys.exit("dw_built out of [0, 1]")
    if not (
        (metrics_df["wc_built"] >= 0).all() and (metrics_df["wc_built"] <= 1).all()
    ):
        sys.exit("wc_built out of [0, 1]")
    ndbi = metrics_df["ndbi"].dropna()
    if not np.isfinite(ndbi).all():
        sys.exit("ndbi contains non-finite values")
    ndbi_lo, ndbi_hi = float(ndbi.min()), float(ndbi.max())
    if ndbi_lo < -1.0 or ndbi_hi > 1.0:
        sys.exit(f"ndbi range [{ndbi_lo:.6f}, {ndbi_hi:.6f}] outside [-1.0, 1.0]")
    if not (
        (panel["built"] >= 0).all() and (panel["built"] <= 1).all()
    ):
        sys.exit("panel built fraction out of [0, 1]")

    metrics_result = result["metrics"]
    for metric in METRICS:
        if metric not in metrics_result:
            sys.exit(f"missing metric {metric} in results")
        m = metrics_result[metric]
        required_m = {
            "linear_cv_mean",
            "nonlinear_cv_mean",
            "mean_gain",
            "folds_favor_nonlinear",
            "nl_selected_lam",
            "lin_selected_lam",
            "nl_fold_scores",
            "lin_fold_scores",
            "fold_differences",
            "negligible_gain",
        }
        missing_m = required_m - set(m.keys())
        if missing_m:
            sys.exit(f"metric {metric} missing keys: {sorted(missing_m)}")
        if len(m["nl_fold_scores"]) != config.CV_FOLDS:
            sys.exit(f"{metric}: nonlinear fold scores != 5")
        if len(m["lin_fold_scores"]) != config.CV_FOLDS:
            sys.exit(f"{metric}: linear fold scores != 5")
        if len(m["fold_differences"]) != config.CV_FOLDS:
            sys.exit(f"{metric}: fold differences != 5")

        for score in m["nl_fold_scores"] + m["lin_fold_scores"]:
            if not np.isfinite(score):
                sys.exit(f"{metric}: non-finite CV R2 score")

        expected_diffs = [
            nl - lin
            for nl, lin in zip(m["nl_fold_scores"], m["lin_fold_scores"])
        ]
        for saved, expected in zip(m["fold_differences"], expected_diffs):
            if abs(saved - expected) > 1e-12:
                sys.exit(
                    f"{metric}: fold_differences do not match nl - lin scores"
                )

        expected_mean = float(np.mean(m["fold_differences"]))
        if abs(m["mean_gain"] - expected_mean) > 1e-12:
            sys.exit(f"{metric}: mean_gain does not match mean of fold_differences")

        expected_favors = int(sum(1 for d in m["fold_differences"] if d > 0))
        if m["folds_favor_nonlinear"] != expected_favors:
            sys.exit(
                f"{metric}: folds_favor_nonlinear does not match fold_differences"
            )

        expected_negligible = bool(expected_mean < 0.005)
        if m["negligible_gain"] != expected_negligible:
            sys.exit(f"{metric}: negligible_gain does not match mean_gain < 0.005")

    csv = pd.read_csv(csv_path)
    required_csv = {
        "metric",
        "metric_label",
        "linear_cv_mean",
        "nonlinear_cv_mean",
        "mean_gain",
        "folds_favor_nonlinear",
        "nl_selected_lam",
        "lin_selected_lam",
        "negligible_gain",
    }
    missing_csv = required_csv - set(csv.columns)
    if missing_csv:
        sys.exit(f"csv missing columns: {sorted(missing_csv)}")

    if len(csv) != len(METRICS):
        sys.exit(f"csv rows={len(csv)} != {len(METRICS)}")

    if not fig_path.exists():
        sys.exit(f"{fig_path} missing")

    print(f"{city}: rq2_metrics.json valid")
    print(f"  subsample: {result['subsample_cells']} cells, {result['subsample_rows']} rows")
    print(f"  metrics rows={len(metrics_df)}, panel rows={len(panel)}")
    print(f"  metrics bounds: dw_built/wc_built in [0,1]; ndbi finite, range [{ndbi_lo:.6f}, {ndbi_hi:.6f}] within [-1.0, 1.0]; panel built in [0,1]")
    print("  Metric comparisons:")
    for metric in METRICS:
        m = metrics_result[metric]
        print(
            f"    {metric}: linear={m['linear_cv_mean']:.4f}, "
            f"nonlinear={m['nonlinear_cv_mean']:.4f}, "
            f"gain={m['mean_gain']:.4f}, "
            f"favors_nonlinear={m['folds_favor_nonlinear']}/5, "
            f"negligible={m['negligible_gain']}"
        )
    print("OK")


if __name__ == "__main__":
    main()
