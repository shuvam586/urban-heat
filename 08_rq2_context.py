import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pygam import LinearGAM, f, s
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold
from scipy.sparse import block_diag
from scipy.sparse.linalg import splu

import config

SUBSAMPLE_CELLS = 10000
SEED = 42
LAM_GRID = np.array([0.1, 1.0, 10.0, 100.0, 1000.0])
N_BOOTSTRAP = 200
BOOTSTRAP_SEED = 42
MIN_CELLS = 500
MIN_BLOCKS = 30
N_EVAL_POINTS = 50

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
CLASS_MAP = {11: 0, 12: 0, 13: 0, 21: 1, 22: 2, 23: 3, 30: 4}
CLASS_LABELS = {
    0: "rural",
    1: "suburban",
    2: "semi-dense",
    3: "dense",
    4: "centre",
}
URBAN_CONTEXTS = ["suburban", "semi-dense", "dense", "centre"]


def block_key_from_xy(x, y):
    key = (
        np.floor(x / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(y / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    return pd.factorize(key)[0]


def subsample_cells_in_context(ctx_df, seed=SEED, max_cells=SUBSAMPLE_CELLS):
    cell_ids = ctx_df["grid_id"].unique()
    rng = np.random.default_rng(seed)
    if len(cell_ids) > max_cells:
        sampled = rng.choice(cell_ids, size=max_cells, replace=False)
    else:
        sampled = cell_ids
    return ctx_df[ctx_df["grid_id"].isin(sampled)].copy()


def make_folds(sub, n_folds=config.CV_FOLDS):
    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    groups = block_key_from_xy(sub["x"].to_numpy(), sub["y"].to_numpy())
    splits = list(GroupKFold(n_splits=n_folds).split(X, y, groups))
    return splits


def cv_scores(terms, X, y, splits, lam):
    scores = []
    for train_index, test_index in splits:
        fold = LinearGAM(terms, lam=lam)
        fold.fit(X[train_index], y[train_index])
        prediction = fold.predict(X[test_index])
        scores.append(float(r2_score(y[test_index], prediction)))
    return scores


def flatten_lam(value):
    if isinstance(value, (list, tuple, np.ndarray)):
        output = []
        for item in value:
            output.extend(flatten_lam(item))
        return output
    return [float(value)]


def flat_lam(lam):
    return flatten_lam(lam)[0]


def derivative_zero_crossings(gam, x_min, x_max, n_points=500):
    xs = np.linspace(x_min, x_max, n_points)
    X_eval = np.column_stack([xs, np.zeros(n_points), np.zeros(n_points)])
    pd_vals = gam.partial_dependence(term=0, X=X_eval)
    pd_vals = np.asarray(pd_vals).ravel()
    dx = xs[1] - xs[0]
    deriv = np.gradient(pd_vals, dx)
    second = np.gradient(deriv, dx)
    crossings = []
    for i in range(1, len(deriv) - 1):
        if deriv[i - 1] < 0 < deriv[i] or deriv[i - 1] > 0 > deriv[i]:
            xc = xs[i]
            xtype = "min" if second[i] > 0 else "max"
            crossings.append({"type": xtype, "built": float(xc)})
    return crossings


def bootstrap_predictions_fast(gam, X_ctx, y_ctx, groups_ctx, X_eval,
                               n_draws, seed, label=""):
    """Fast block-bootstrap using precomputed design matrix.

    Fits GAM once to get design matrix Z and combined penalty P_total.
    Each bootstrap draw resamples blocks, then solves the penalized
    least squares system directly: coef = (Z_draw' Z_draw + P_total)^-1 Z_draw' y_draw.
    """
    rng = np.random.default_rng(seed)
    unique_blocks = np.unique(groups_ctx)
    n_blocks = len(unique_blocks)
    block_to_idx = {b: np.where(groups_ctx == b)[0] for b in unique_blocks}

    # Full design matrix (N x K) and eval matrix (N_eval x K)
    Z = gam._modelmat(X_ctx)
    Z_eval = gam._modelmat(X_eval)
    n_coefs = gam.coef_.shape[0]

    # Combined penalty matrix: block-diagonal of lam_j * P_j per term
    penalty_blocks = []
    offset = 0
    for j, term in enumerate(gam.terms):
        n_j = term.n_coefs
        P_j = term.build_penalties()
        if hasattr(P_j, "toarray"):
            P_j = P_j.toarray()
        P_j = np.asarray(P_j, dtype=float)
        term_lam_vals = flatten_lam(term.lam) if term.lam is not None else [0.0]
        term_lam = term_lam_vals[0] if term_lam_vals else 0.0
        penalty_blocks.append(term_lam * P_j)
        offset += n_j
    P_total = block_diag(penalty_blocks).toarray()

    draws = np.full((n_draws, len(X_eval)), np.nan)
    t0 = time.time()
    for draw in range(n_draws):
        drawn = rng.choice(unique_blocks, size=n_blocks, replace=True)
        train_idx = np.concatenate([block_to_idx[b] for b in drawn])
        Z_draw = Z[train_idx, :]
        y_draw = y_ctx[train_idx]
        A = Z_draw.T @ Z_draw + P_total
        b_vec = Z_draw.T @ y_draw
        coef_draw = np.linalg.solve(A, b_vec)
        draws[draw, :] = Z_eval @ coef_draw
        if (draw + 1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"    {label} bootstrap draw {draw + 1}/{n_draws} "
                  f"({elapsed:.1f}s elapsed)")
    lower = np.percentile(draws, 2.5, axis=0)
    upper = np.percentile(draws, 97.5, axis=0)
    return lower, upper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, choices=sorted(config.CITIES))
    args = parser.parse_args()

    city = args.city
    panel = pd.read_parquet(Path("data") / city / "panel.parquet")
    output_dir = Path("outputs") / city
    output_dir.mkdir(parents=True, exist_ok=True)

    year_levels = sorted(int(year) for year in panel["year"].unique())
    panel["year_code"] = panel["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )
    year_2022_code = year_levels.index(2022) if 2022 in year_levels else 0
    city_median_ndvi = float(panel["ndvi"].median())

    # ===== Part A: Within-context smooths (H6) =====
    coverage = []
    context_results = []
    csv_rows = []

    for code in range(len(CLASS_ORDER)):
        label = CLASS_LABELS[code]
        ctx_full = panel[panel["ladder_class"].map(CLASS_MAP) == code].copy()
        n_cells = int(ctx_full["grid_id"].nunique())
        ctx_blocks = block_key_from_xy(
            ctx_full["x"].to_numpy(), ctx_full["y"].to_numpy()
        )
        n_blocks = int(len(np.unique(ctx_blocks)))
        q01 = float(ctx_full["built"].quantile(0.01))
        q99 = float(ctx_full["built"].quantile(0.99))
        eligible = bool(n_cells >= MIN_CELLS and n_blocks >= MIN_BLOCKS)

        coverage.append(
            {
                "context": label,
                "n_cells": n_cells,
                "n_blocks": n_blocks,
                "built_q05": q01,
                "built_q099": q99,
                "eligible": eligible,
            }
        )

        if not eligible:
            context_results.append(
                {
                    "context": label,
                    "eligible": False,
                    "reason": f"cells={n_cells} blocks={n_blocks}",
                }
            )
            continue

        ctx_sub = subsample_cells_in_context(ctx_full, seed=SEED)
        ctx_sub["year_code"] = ctx_sub["year"].map(
            {year: code2 for code2, year in enumerate(year_levels)}
        )
        X_ctx = ctx_sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
        y_ctx = ctx_sub["lst_rel"].to_numpy(dtype=float)
        groups_ctx = block_key_from_xy(
            ctx_sub["x"].to_numpy(), ctx_sub["y"].to_numpy()
        )

        gam = LinearGAM(s(0) + s(1) + f(2))
        gam.gridsearch(X_ctx, y_ctx, lam=LAM_GRID, progress=False)
        selected_lam = flat_lam(gam.lam)

        built_eval = np.linspace(q01, q99, N_EVAL_POINTS)
        X_eval = np.column_stack(
            [
                built_eval,
                np.full(N_EVAL_POINTS, city_median_ndvi),
                np.full(N_EVAL_POINTS, float(year_2022_code)),
            ]
        )

        gam_full = LinearGAM(s(0) + s(1) + f(2), lam=selected_lam)
        gam_full.fit(X_ctx, y_ctx)
        pred = gam_full.predict(X_eval)

        ci_low, ci_high = bootstrap_predictions_fast(
            gam_full,
            X_ctx,
            y_ctx,
            groups_ctx,
            X_eval,
            N_BOOTSTRAP,
            BOOTSTRAP_SEED,
            label=label,
        )

        context_results.append(
            {
                "context": label,
                "eligible": True,
                "n_cells": n_cells,
                "n_blocks": n_blocks,
                "built_q01": q01,
                "built_q099": q99,
                "median_ndvi": city_median_ndvi,
                "selected_lam": selected_lam,
                "n_cells_subsampled": int(ctx_sub["grid_id"].nunique()),
                "n_rows_subsampled": int(len(ctx_sub)),
            }
        )

        for i in range(N_EVAL_POINTS):
            csv_rows.append(
                {
                    "context": label,
                    "eligible": True,
                    "built": float(built_eval[i]),
                    "pred": float(pred[i]),
                    "ci_low": float(ci_low[i]),
                    "ci_high": float(ci_high[i]),
                    "reason": "",
                }
            )

    # Overlap ranges
    eligible_contexts = [c for c in context_results if c["eligible"]]
    all_q01 = max(c["built_q01"] for c in eligible_contexts)
    all_q099 = min(c["built_q099"] for c in eligible_contexts)
    urban_contexts = [c for c in eligible_contexts if c["context"] in URBAN_CONTEXTS]
    urban_q01 = max(c["built_q01"] for c in urban_contexts) if urban_contexts else None
    urban_q099 = min(c["built_q099"] for c in urban_contexts) if urban_contexts else None

    # ===== Part B: Formal nonlinearity check (H2) =====
    cell_ids = panel["grid_id"].unique()
    rng = np.random.default_rng(SEED)
    if len(cell_ids) > SUBSAMPLE_CELLS:
        sampled_cells = rng.choice(cell_ids, size=SUBSAMPLE_CELLS, replace=False)
    else:
        sampled_cells = cell_ids
    sub = panel[panel["grid_id"].isin(sampled_cells)].copy()
    sub["year_code"] = sub["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )
    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    groups = block_key_from_xy(sub["x"].to_numpy(), sub["y"].to_numpy())
    splits = make_folds(sub, n_folds=config.CV_FOLDS)

    from pygam import s as _s

    linear_terms_pygam = _s(0, spline_order=1) + _s(1) + f(2)
    nonlinear_terms_pygam = _s(0) + _s(1) + f(2)

    linear_gam = LinearGAM(linear_terms_pygam)
    linear_gam.gridsearch(X, y, lam=LAM_GRID, progress=False)
    linear_lam = flat_lam(linear_gam.lam)

    nonlinear_gam = LinearGAM(nonlinear_terms_pygam)
    nonlinear_gam.gridsearch(X, y, lam=LAM_GRID, progress=False)
    nonlinear_lam = flat_lam(nonlinear_gam.lam)

    linear_scores = cv_scores(linear_terms_pygam, X, y, splits, linear_lam)
    nonlinear_scores = cv_scores(nonlinear_terms_pygam, X, y, splits, nonlinear_lam)

    fold_differences = [
        nl - lin for nl, lin in zip(nonlinear_scores, linear_scores)
    ]
    mean_gain = float(np.mean(fold_differences))
    folds_favour_nonlinear = int(sum(1 for d in fold_differences if d > 0))
    negligible_gain = bool(mean_gain < 0.005)

    q01_all, q99_all = float(panel["built"].quantile(0.01)), float(
        panel["built"].quantile(0.99)
    )
    zero_crossings = derivative_zero_crossings(
        nonlinear_gam, q01_all, q99_all
    )

    part_b = {
        "model_nonlinear": "s(built) + s(ndvi) + f(year)",
        "model_linear": "built + s(ndvi) + f(year)",
        "nl_selected_lam": nonlinear_lam,
        "lin_selected_lam": linear_lam,
        "nl_fold_scores": nonlinear_scores,
        "lin_fold_scores": linear_scores,
        "fold_differences": fold_differences,
        "mean_gain": mean_gain,
        "folds_favour_nonlinear": folds_favour_nonlinear,
        "negligible_gain": negligible_gain,
        "derivative_zero_crossings": zero_crossings,
        "subsample_cells": int(sub["grid_id"].nunique()),
        "subsample_rows": int(len(sub)),
    }

    # ===== Save outputs =====
    context_csv = pd.DataFrame(csv_rows)
    context_csv.to_csv(output_dir / "rq2_context.csv", index=False)

    result = {
        "city": city,
        "subsample_cells": int(sub["grid_id"].nunique()),
        "subsample_rows": int(len(sub)),
        "n_folds": config.CV_FOLDS,
        "block_size_m": config.BLOCK_SIZE_M,
        "lam_grid": [float(v) for v in LAM_GRID],
        "n_bootstrap": N_BOOTSTRAP,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "city_median_ndvi": city_median_ndvi,
        "coverage": coverage,
        "context_results": context_results,
        "part_b": part_b,
        "overlap_all": {
            "q01": float(all_q01),
            "q099": float(all_q099),
            "n_contexts": len(eligible_contexts),
        },
        "overlap_urban": {
            "q01": float(urban_q01) if urban_q01 is not None else None,
            "q099": float(urban_q099) if urban_q099 is not None else None,
            "n_contexts": len(urban_contexts),
        },
    }
    with open(output_dir / "rq2_context.json", "w") as handle:
        json.dump(result, handle, indent=2)

    # Figure 5
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, cr in enumerate(context_results):
        if not cr["eligible"]:
            continue
        label = cr["context"]
        rows = context_csv[
            (context_csv["context"] == label) & (context_csv["eligible"])
        ]
        if rows.empty:
            continue
        color = colors[i % len(colors)]
        ax.plot(
            rows["built"],
            rows["pred"],
            color=color,
            label=label,
            linewidth=1.5,
        )
        ax.fill_between(
            rows["built"],
            rows["ci_low"],
            rows["ci_high"],
            color=color,
            alpha=0.15,
        )
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Built-up fraction")
    ax.set_ylabel("Partial built effect (K)")
    ax.set_title(
        f"{city}: within-context built-up response (H6)\n"
        "year 2022, city-median NDVI; shaded = 95% block bootstrap"
    )
    ax.legend(loc="best")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_dir / "fig5_rq2_context.png", dpi=150)
    plt.close(fig)

    print(f"{city}: wrote {output_dir / 'rq2_context.csv'}")
    print(f"{city}: wrote {output_dir / 'rq2_context.json'}")
    print(f"{city}: wrote {output_dir / 'fig5_rq2_context.png'}")
    print(f"subsample: {result['subsample_cells']} cells, {result['subsample_rows']} rows")
    print("Part A coverage:")
    for c in coverage:
        print(
            f"  {c['context']}: cells={c['n_cells']}, blocks={c['n_blocks']}, "
            f"built[{c['built_q05']:.3f},{c['built_q099']:.3f}], "
            f"eligible={c['eligible']}"
        )
    print("  overlap_all:", result["overlap_all"])
    print("  overlap_urban:", result["overlap_urban"])
    print("Part B:")
    print(
        f"  nonlinear lam={nonlinear_lam}, linear lam={linear_lam}"
    )
    print(
        f"  mean gain={mean_gain:.6f}, folds favour nonlinear={folds_favour_nonlinear}/5, "
        f"negligible={negligible_gain}"
    )
    print(f"  zero crossings: {zero_crossings}")


if __name__ == "__main__":
    main()
