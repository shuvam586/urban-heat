import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
CLASS_CODES = [
    "rural\n(11-13)",
    "suburban\n(21)",
    "semi-dense\n(22)",
    "dense\n(23)",
    "centre\n(30)",
]
CLASS_MAP = {11: 0, 12: 0, 13: 0, 21: 1, 22: 2, 23: 3, 30: 4}


def block_bootstrap(x, y_coord, values, group, n_draws, percentiles, seed):
    block_key = (
        np.floor(x / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(y_coord / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    block_codes = pd.factorize(block_key)[0]
    n_blocks = int(block_codes.max()) + 1
    rng = np.random.default_rng(seed)
    draws = np.full((n_draws, len(CLASS_ORDER)), np.nan)
    for draw in range(n_draws):
        counts = np.bincount(
            rng.integers(0, n_blocks, size=n_blocks),
            minlength=n_blocks,
        )
        weights = counts[block_codes]
        sample_values = np.repeat(values, weights)
        classes = np.repeat(group, weights)
        for code in range(len(CLASS_ORDER)):
            subset = sample_values[classes == code]
            if len(subset):
                draws[draw, code] = np.median(subset)
    low, high = np.nanpercentile(draws, percentiles, axis=0)
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
    rng_seed = 42
    for year in config.YEARS:
        sub = panel[panel["year"] == year].reset_index(drop=True)
        x = sub["x"].to_numpy()
        y = sub["y"].to_numpy()
        values = sub["lst_rel"].to_numpy()
        group = sub["class_group"].to_numpy().astype(int)

        low, high = block_bootstrap(
            x,
            y,
            values,
            group,
            config.BOOTSTRAP_DRAWS,
            config.BOOTSTRAP_PERCENTILES,
            rng_seed,
        )
        rng_seed += 1

        for code, name in enumerate(CLASS_ORDER):
            subset = values[group == code]
            rows.append(
                {
                    "year": year,
                    "class": name,
                    "median": float(np.median(subset)),
                    "ci_low": float(low[code]),
                    "ci_high": float(high[code]),
                    "n_cells": int(len(subset)),
                }
            )

    gradient = pd.DataFrame(rows)
    gradient.to_csv(output_dir / "gradient.csv", index=False)

    y_low, y_high = panel["lst_rel"].quantile([0.01, 0.99])
    pad = 0.05 * (y_high - y_low)
    y_limits = (y_low - pad, y_high + pad)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, year in zip(axes, config.YEARS):
        sub = panel[panel["year"] == year]
        year_rows = gradient[gradient["year"] == year].set_index("class")
        data = [
            sub.loc[sub["class_group"] == code, "lst_rel"].to_numpy()
            for code in range(len(CLASS_ORDER))
        ]
        ax.boxplot(
            data,
            positions=range(len(CLASS_ORDER)),
            widths=0.6,
            showfliers=False,
            patch_artist=True,
            boxprops={"facecolor": "#d9e6f2", "edgecolor": "#333333"},
            whiskerprops={"color": "#333333"},
            capprops={"color": "#333333"},
            medianprops={"color": "#b22222", "linewidth": 1.5},
        )
        medians = year_rows.loc[CLASS_ORDER, "median"].to_numpy()
        lows = year_rows.loc[CLASS_ORDER, "ci_low"].to_numpy()
        highs = year_rows.loc[CLASS_ORDER, "ci_high"].to_numpy()
        ax.vlines(
            range(len(CLASS_ORDER)),
            lows,
            highs,
            color="black",
            linewidth=1.5,
            label="95% block bootstrap",
        )
        ax.plot(
            range(len(CLASS_ORDER)),
            medians,
            "o",
            color="black",
            markersize=4,
        )
        ax.axhline(0, color="grey", linewidth=1, linestyle="--")
        ax.set_xticks(range(len(CLASS_ORDER)))
        ax.set_xticklabels(CLASS_CODES)
        ax.set_title(str(year))
        ax.set_ylim(*y_limits)
        ax.grid(axis="y", alpha=0.2)
        if ax is axes[0]:
            ax.set_ylabel("LST relative to rural median (K)")
            ax.legend(loc="lower left", fontsize=8)

    fig.suptitle("Hyderabad: LST relative to rural median by ladder class")
    fig.tight_layout()
    fig.savefig(output_dir / "fig1_gradient.png", dpi=150)

    print(f"{city}: wrote {output_dir / 'gradient.csv'}")
    print(f"{city}: wrote {output_dir / 'fig1_gradient.png'}")
    print(gradient.to_string(index=False))


if __name__ == "__main__":
    main()
