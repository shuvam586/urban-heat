import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
CLASS_MAP = {11: 0, 12: 0, 13: 0, 21: 1, 22: 2, 23: 3, 30: 4}
REFERENCES = ["Ref_A", "Ref_B", "Ref_C"]
REF_COLORS = {"Ref_A": "#1f77b4", "Ref_B": "#d62728", "Ref_C": "#2ca02c"}
RURAL_CODES = (11, 12, 13)
SEED = 42


def block_codes(x, y):
    key = (
        np.floor(x / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(y / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    return pd.factorize(key)[0]


def reference_mask(sub, year, ref, ref_a_ndvi_median):
    if ref == "Ref_A":
        return sub["smod"].isin(RURAL_CODES)
    if ref == "Ref_B":
        return sub["smod"] == 11
    if ref == "Ref_C":
        return (
            sub["smod"].isin(RURAL_CODES)
            & (sub["built"] < 0.05)
            & (sub["ndvi"] >= ref_a_ndvi_median)
        )
    raise ValueError(f"unknown reference: {ref}")


def reference_bootstrap(x, y, lst_k, class_group, ref_mask, n_draws, percentiles, seed):
    """Resample 5 km blocks with replacement; recompute the reference median
    within each draw; return per-class (median lst_k - ref median) draws."""
    codes = block_codes(x, y)
    n_blocks = int(codes.max()) + 1
    rng = np.random.default_rng(seed)
    draws = np.full((n_draws, len(CLASS_ORDER)), np.nan)
    ref_vals = lst_k[ref_mask]
    ref_codes = codes[ref_mask]
    for draw in range(n_draws):
        counts = np.bincount(
            rng.integers(0, n_blocks, size=n_blocks), minlength=n_blocks
        )
        weights = counts[codes]
        rep_ref = np.repeat(ref_vals, weights[ref_mask])
        ref_med = np.median(rep_ref)
        for code in range(len(CLASS_ORDER)):
            cls_mask = class_group == code
            cls_vals = lst_k[cls_mask]
            cls_w = weights[cls_mask]
            rep = np.repeat(cls_vals, cls_w)
            if len(rep):
                draws[draw, code] = np.median(rep) - ref_med
    low, high = np.percentile(draws, percentiles, axis=0)
    return low, high


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    panel = pd.read_parquet(Path("data") / city / "panel.parquet")
    panel["class_group"] = panel["ladder_class"].map(CLASS_MAP)
    if panel["class_group"].isna().any():
        raise SystemExit("unmapped ladder classes in panel")

    output_dir = Path("outputs") / city
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for year in config.YEARS:
        sub = panel[panel["year"] == year].reset_index(drop=True)
        x = sub["x"].to_numpy()
        y = sub["y"].to_numpy()
        lst_k = sub["lst_k"].to_numpy()
        class_group = sub["class_group"].to_numpy().astype(int)
        ref_a_ndvi_median = float(
            np.median(sub.loc[sub["smod"].isin(RURAL_CODES), "ndvi"])
        )

        for ref in REFERENCES:
            ref_mask = reference_mask(
                sub, year, ref, ref_a_ndvi_median
            ).to_numpy()
            ref_n_cells = int(ref_mask.sum())
            ref_n_blocks = int(len(np.unique(block_codes(x, y)[ref_mask])))
            if ref_n_cells < 200:
                raise SystemExit(
                    f"{city} {year} {ref}: reference group has {ref_n_cells} cells, fewer than 200"
                )
            if ref_n_blocks < 30:
                raise SystemExit(
                    f"{city} {year} {ref}: reference group has {ref_n_blocks} distinct 5 km blocks, fewer than 30"
                )

            low, high = reference_bootstrap(
                x,
                y,
                lst_k,
                class_group,
                ref_mask,
                config.BOOTSTRAP_DRAWS,
                config.BOOTSTRAP_PERCENTILES,
                SEED,
            )
            ref_med = float(np.median(lst_k[ref_mask]))
            for code, name in enumerate(CLASS_ORDER):
                cls_vals = lst_k[class_group == code]
                rows.append(
                    {
                        "year": year,
                        "reference": ref,
                        "class": name,
                        "median": float(np.median(cls_vals) - ref_med),
                        "ci_low": float(low[code]),
                        "ci_high": float(high[code]),
                        "n_cells": int(len(cls_vals)),
                        "ref_n_cells": ref_n_cells,
                        "ref_n_blocks": ref_n_blocks,
                    }
                )

    rq1 = pd.DataFrame(rows)
    rq1.to_csv(output_dir / "rq1_references.csv", index=False)

    y_low = float(rq1["ci_low"].min())
    y_high = float(rq1["ci_high"].max())
    pad = 0.05 * (y_high - y_low)
    y_limits = (y_low - pad, y_high + pad)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    offsets = np.arange(len(CLASS_ORDER))
    width = 0.2
    for ax, year in zip(axes, config.YEARS):
        for i, ref in enumerate(REFERENCES):
            s = (
                rq1[(rq1["year"] == year) & (rq1["reference"] == ref)]
                .set_index("class")
                .loc[CLASS_ORDER]
            )
            medians = s["median"].to_numpy()
            lows = s["ci_low"].to_numpy()
            highs = s["ci_high"].to_numpy()
            pos = offsets + (i - 1) * width
            ax.errorbar(
                pos,
                medians,
                yerr=[medians - lows, highs - medians],
                fmt="o",
                color=REF_COLORS[ref],
                label=ref,
                capsize=3,
                markersize=4,
                elinewidth=1,
            )
            ax.vlines(pos, lows, highs, color=REF_COLORS[ref], linewidth=1)
        ax.axhline(0, color="grey", linewidth=1, linestyle="--")
        ax.set_xticks(offsets)
        ax.set_xticklabels(
            CLASS_ORDER, rotation=45, ha="right", fontsize=8
        )
        ax.set_title(str(year))
        ax.set_ylim(*y_limits)
        ax.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Median lst_rel (K)")
    axes[0].legend(fontsize=8, title="rural reference")
    fig.suptitle(
        f"{city}: rural reference sensitivity (RQ1), "
        f"{config.BOOTSTRAP_DRAWS} block-bootstrap draws, seed {SEED}"
    )
    fig.tight_layout()
    fig.savefig(output_dir / "fig4_rq1_references.png", dpi=150)

    print(f"{city}: wrote {output_dir / 'rq1_references.csv'}")
    print(f"{city}: wrote {output_dir / 'fig4_rq1_references.png'}")
    print(rq1.to_string(index=False))


if __name__ == "__main__":
    main()
