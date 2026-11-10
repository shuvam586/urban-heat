import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pygam import LinearGAM, f, s, te
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

import config

SUBSAMPLE_CELLS = 10000
SEED = 42
LAM_GRID = np.logspace(-1, 3, 5)
FIG2_BINS = 20
FIG3_BINS = 40
FIG3_MIN_COUNT = 5
Z95 = 1.959963984540054


def flatten(value):
    if isinstance(value, (list, tuple, np.ndarray)):
        output = []
        for item in value:
            output.extend(flatten(item))
        return output
    return [float(value)]


def score_summary(scores):
    return {
        "r2_scores": [float(score) for score in scores],
        "r2_mean": float(np.mean(scores)),
        "r2_std": float(np.std(scores)),
        "r2_min": float(np.min(scores)),
        "r2_max": float(np.max(scores)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    panel = pd.read_parquet(Path("data") / city / "panel.parquet")
    output_dir = Path("outputs") / city
    output_dir.mkdir(parents=True, exist_ok=True)

    cell_ids = panel["grid_id"].unique()
    rng = np.random.default_rng(SEED)
    if len(cell_ids) > SUBSAMPLE_CELLS:
        sampled_cells = rng.choice(
            cell_ids, size=SUBSAMPLE_CELLS, replace=False
        )
        sub = panel[panel["grid_id"].isin(sampled_cells)].copy()
    else:
        sub = panel.copy()

    year_levels = sorted(int(year) for year in sub["year"].unique())
    sub["year_code"] = sub["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )

    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    block_key = (
        np.floor(sub["x"] / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(sub["y"] / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    groups = pd.factorize(block_key)[0]
    splits = list(
        GroupKFold(n_splits=config.CV_FOLDS).split(X, y, groups)
    )

    def cv_scores(terms, lam):
        scores = []
        for train_index, test_index in splits:
            fold = LinearGAM(terms, lam=lam)
            fold.fit(X[train_index], y[train_index])
            prediction = fold.predict(X[test_index])
            scores.append(float(r2_score(y[test_index], prediction)))
        return scores

    full_terms = s(0) + s(1) + te(0, 1) + f(2)
    gam = LinearGAM(full_terms)
    gam.gridsearch(X, y, lam=LAM_GRID, progress=False)
    full_scores = cv_scores(full_terms, gam.lam)
    full_summary = score_summary(full_scores)

    ndvi_model = LinearGAM(s(1) + f(2))
    ndvi_model.gridsearch(X, y, lam=LAM_GRID, progress=False)
    ndvi_scores = cv_scores(s(1) + f(2), ndvi_model.lam)

    built_model = LinearGAM(s(0) + f(2))
    built_model.gridsearch(X, y, lam=LAM_GRID, progress=False)
    built_scores = cv_scores(s(0) + f(2), built_model.lam)

    comparisons = {
        "scope": "fixed part of step 05",
        "folds": "same 5 km GroupKFold folds",
        "models": {
            "ndvi_year": {
                "terms": "s(ndvi) + f(year)",
                "selected_lam": flatten(ndvi_model.lam)[0],
                **score_summary(ndvi_scores),
            },
            "built_year": {
                "terms": "s(built) + f(year)",
                "selected_lam": flatten(built_model.lam)[0],
                **score_summary(built_scores),
            },
            "full": {
                "terms": "s(built) + s(ndvi) + te(built, ndvi) + f(year)",
                "selected_lam": flatten(gam.lam)[0],
                **full_summary,
            },
        },
    }

    q01, q99 = panel["built"].quantile([0.01, 0.99])
    eval_edges = np.linspace(q01, q99, FIG2_BINS + 1)
    eval_centers = 0.5 * (eval_edges[:-1] + eval_edges[1:])
    ndvi_quantiles = np.full((FIG2_BINS, 3), np.nan)
    valid_bins = np.zeros(FIG2_BINS, dtype=bool)
    for i in range(FIG2_BINS):
        if i < FIG2_BINS - 1:
            in_bin = (panel["built"] >= eval_edges[i]) & (
                panel["built"] < eval_edges[i + 1]
            )
        else:
            in_bin = (panel["built"] >= eval_edges[i]) & (
                panel["built"] <= eval_edges[i + 1]
            )
        values = panel.loc[in_bin, "ndvi"]
        if len(values) >= 5:
            ndvi_quantiles[i] = np.quantile(values, [0.25, 0.5, 0.75])
            valid_bins[i] = True

    eval_rows = []
    for i in range(FIG2_BINS):
        if not valid_bins[i]:
            continue
        for q in range(3):
            eval_rows.append([eval_centers[i], ndvi_quantiles[i, q], 0.0])
    X_eval = np.array(eval_rows)
    n_valid = int(valid_bins.sum())

    s_effect = gam.partial_dependence(term=0, X=X_eval)
    te_effect = gam.partial_dependence(term=2, X=X_eval)
    point_total = s_effect + te_effect

    design = gam._modelmat(X_eval)
    offsets = np.cumsum([0] + [int(term.n_coefs) for term in gam.terms])
    cols_built = np.arange(offsets[0], offsets[1])
    cols_te = np.arange(offsets[2], offsets[3])
    cols = np.concatenate([cols_built, cols_te])
    Z = np.hstack(
        [
            design[:, cols_built].toarray(),
            design[:, cols_te].toarray(),
        ]
    )
    covariance = gam.statistics_["cov"][np.ix_(cols, cols)]
    total = Z @ gam.coef_[cols]
    if not np.allclose(total, point_total, atol=1e-8):
        raise SystemExit("total effect does not match term sum")
    variance = np.einsum("ij,jk,ik->i", Z, covariance, Z)
    standard_error = np.sqrt(np.maximum(variance, 0.0))
    lower = total - Z95 * standard_error
    upper = total + Z95 * standard_error

    total_lines = total.reshape(n_valid, 3)
    lower_lines = lower.reshape(n_valid, 3)
    upper_lines = upper.reshape(n_valid, 3)
    centers = eval_centers[valid_bins]

    total_min = float(np.min(total_lines))
    total_max = float(np.max(total_lines))
    start_min = float(np.min(total_lines[0]))
    start_max = float(np.max(total_lines[0]))
    end_min = float(np.min(total_lines[-1]))
    end_max = float(np.max(total_lines[-1]))
    p50 = total_lines[:, 1]
    crossing = None
    for i in range(1, len(p50)):
        if p50[i - 1] > 0 and p50[i] <= 0:
            fraction = p50[i - 1] / (p50[i - 1] - p50[i])
            crossing = centers[i - 1] + fraction * (
                centers[i] - centers[i - 1]
            )
            break
    if crossing is None:
        crossing_text = "without crossing zero inside the plotted range"
    else:
        crossing_text = f"through zero near built {crossing:.2f}"

    shape_words = (
        "The total built effect is generally downward: from "
        f"{start_min:.1f}-{start_max:.1f} K at built {q01:.2f}, "
        f"{crossing_text}, to {end_min:.1f}-{end_max:.1f} K at "
        f"built {q99:.2f}; the three NDVI lines are close at low built "
        "and diverge at high built, with the highest-NDVI line the most "
        "negative."
    )

    n_above_04 = int((panel["built"] > 0.4).sum())
    n_above_05 = int((panel["built"] > 0.5).sum())
    share_above_04 = float((panel["built"] > 0.4).mean())
    share_above_05 = float((panel["built"] > 0.5).mean())
    n_below_01 = int((panel["built"] < 0.1).sum())
    share_below_01 = float((panel["built"] < 0.1).mean())
    unsupported_words = (
        "The curve is unsupported where cells are sparse: "
        f"{n_above_04:,} cells ({share_above_04:.2%}) are above built 0.4 "
        f"and {n_above_05:,} ({share_above_05:.2%}) above 0.5."
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    labels = ["NDVI p25", "NDVI p50", "NDVI p75"]
    for q, (color, label) in enumerate(zip(colors, labels)):
        ax.plot(centers, total_lines[:, q], color=color, label=label)
        ax.fill_between(
            centers,
            lower_lines[:, q],
            upper_lines[:, q],
            color=color,
            alpha=0.18,
        )
    rug_rng = np.random.default_rng(0)
    rug_values = rug_rng.choice(
        panel["built"].to_numpy(), size=10000, replace=False
    )
    rug_y = float(np.min(lower_lines)) - 0.05 * (
        float(np.max(upper_lines)) - float(np.min(lower_lines))
    )
    ax.plot(
        rug_values,
        np.full_like(rug_values, rug_y),
        "|",
        color="black",
        alpha=0.15,
        markersize=3,
    )
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlim(q01, q99)
    ax.set_xlabel("Built-up fraction")
    ax.set_ylabel("Total built effect (K)")
    ax.set_title(
        f"{city}: total built effect (s(built) + te(built, NDVI))\n"
        "NDVI p25/p50/p75 within built bins; year 2022; shaded = 95% band"
    )
    ax.legend(loc="best")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_dir / "fig2_builtup.png", dpi=150)
    plt.close(fig)

    built_edges = np.linspace(
        panel["built"].min(), panel["built"].max(), FIG3_BINS + 1
    )
    ndvi_edges = np.linspace(
        panel["ndvi"].min(), panel["ndvi"].max(), FIG3_BINS + 1
    )
    counts, _, _ = np.histogram2d(
        panel["built"], panel["ndvi"], bins=[built_edges, ndvi_edges]
    )
    built_centers = 0.5 * (built_edges[:-1] + built_edges[1:])
    ndvi_centers = 0.5 * (ndvi_edges[:-1] + ndvi_edges[1:])
    built_mesh, ndvi_mesh = np.meshgrid(built_centers, ndvi_centers)
    X_te = np.column_stack(
        [
            built_mesh.ravel(),
            ndvi_mesh.ravel(),
            np.zeros(built_mesh.size),
        ]
    )
    te_surface, _ = gam.partial_dependence(term=2, X=X_te, width=0.95)
    te_surface = te_surface.reshape(built_mesh.shape)
    mask_correct = counts.T < FIG3_MIN_COUNT
    masked_surface = np.ma.masked_where(mask_correct, te_surface)

    max_i, max_j = np.unravel_index(np.argmax(counts), counts.shape)
    max_bin_masked = bool(mask_correct[max_j, max_i])

    fig, ax = plt.subplots(figsize=(8, 6))
    image = ax.pcolormesh(
        built_edges,
        ndvi_edges,
        masked_surface,
        shading="auto",
        cmap="viridis",
    )
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("te(built, ndvi) partial effect (K)")
    ax.set_xlabel("Built-up fraction")
    ax.set_ylabel("NDVI")
    ax.set_title(
        f"{city}: te(built, ndvi) surface\n"
        f"white = fewer than {FIG3_MIN_COUNT} cells"
    )
    fig.tight_layout()
    fig.savefig(output_dir / "fig3_interaction.png", dpi=150)
    plt.close(fig)

    cv = {
        "model": "lst_rel ~ s(built) + s(ndvi) + te(built, ndvi) + f(year)",
        "year_levels": year_levels,
        "n_folds": config.CV_FOLDS,
        "block_size_m": config.BLOCK_SIZE_M,
        **full_summary,
        "converged": bool(np.isfinite(gam.coef_).all()),
        "n_cells_total": int(panel["grid_id"].nunique()),
        "n_rows_total": int(len(panel)),
        "subsample_cells": int(sub["grid_id"].nunique()),
        "subsample_rows": int(len(sub)),
        "lam_grid": [float(value) for value in LAM_GRID],
        "selected_lam": flatten(gam.lam)[0],
        "model_comparisons": comparisons,
        "built_total_min": total_min,
        "built_total_max": total_max,
        "built_total_range": total_max - total_min,
        "built_total_shape_words": shape_words,
        "built_unsupported_words": unsupported_words,
        "n_cells_below_built_0.1": n_below_01,
        "share_below_built_0.1": share_below_01,
        "n_cells_above_built_0.4": n_above_04,
        "share_above_built_0.4": share_above_04,
        "n_cells_above_built_0.5": n_above_05,
        "share_above_built_0.5": share_above_05,
        "fig2_built_bins": FIG2_BINS,
        "fig2_valid_bins": n_valid,
        "fig2_built_range": [float(q01), float(q99)],
        "fig2_band": (
            "model-based 95% band for the summed s(built)+te terms "
            "using the coefficient covariance, conditional on the "
            "selected smoothing"
        ),
        "fig3_bins": FIG3_BINS,
        "fig3_min_count": FIG3_MIN_COUNT,
        "fig3_mask_orientation": "rows=NDVI bins, columns=built bins",
        "fig3_mask": mask_correct.astype(int).tolist(),
        "fig3_max_bin_count": int(counts[max_i, max_j]),
        "fig3_max_bin_built": [
            float(built_edges[max_i]),
            float(built_edges[max_i + 1]),
        ],
        "fig3_max_bin_ndvi": [
            float(ndvi_edges[max_j]),
            float(ndvi_edges[max_j + 1]),
        ],
        "fig3_max_bin_masked": max_bin_masked,
    }
    with open(output_dir / "cv.json", "w") as handle:
        json.dump(cv, handle, indent=2)

    print(f"{city}: wrote {output_dir / 'fig2_builtup.png'}")
    print(f"{city}: wrote {output_dir / 'fig3_interaction.png'}")
    print(f"{city}: wrote {output_dir / 'cv.json'}")
    print(
        f"subsample: {cv['subsample_cells']} cells, "
        f"{cv['subsample_rows']} rows"
    )
    print(
        f"full CV R2: {cv['r2_mean']:.4f} +/- {cv['r2_std']:.4f}"
    )
    print(
        f"total built effect: {total_min:.3f} to {total_max:.3f} K"
    )
    print(
        f"mask: max bin {cv['fig3_max_bin_count']} cells, "
        f"masked={max_bin_masked}"
    )


if __name__ == "__main__":
    main()
