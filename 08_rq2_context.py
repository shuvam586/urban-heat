import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pygam import LinearGAM, f, s
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

import config

SUBSAMPLE_CELLS = 10000
SEED = 42
LAM_GRID = np.array([0.1, 1.0, 10.0, 100.0, 1000.0])
N_BOOTSTRAP = 200
BOOTSTRAP_SEED = 42
MIN_CELLS = 500
MIN_BLOCKS = 30
N_EVAL_POINTS = 50
Z95 = 1.959963984540054

CLASS_ORDER = ["rural", "suburban", "semi-dense", "dense", "centre"]
CLASS_MAP = {11: 0, 12: 0, 13: 0, 21: 1, 22: 2, 23: 3, 30: 4}
CLASS_LABELS = {
    0: "rural",
    1: "suburban",
    2: "semi-dense",
    3: "dense",
    4: "centre",
}


def block_key_from_xy(x, y):
    key = (
        np.floor(x / config.BLOCK_SIZE_M).astype(int).astype(str)
        + "_"
        + np.floor(y / config.BLOCK_SIZE_M).astype(int).astype(str)
    )
    return pd.factorize(key)[0]


def subsample_panel(panel, seed=SEED, max_cells=SUBSAMPLE_CELLS):
    """Reproduce the exact step-05 subsample: 10,000 cells, all rows for them."""
    cell_ids = panel["grid_id"].unique()
    rng = np.random.default_rng(seed)
    if len(cell_ids) > max_cells:
        sampled_cells = rng.choice(cell_ids, size=max_cells, replace=False)
    else:
        sampled_cells = cell_ids
    sub = panel[panel["grid_id"].isin(sampled_cells)].copy()
    return sub, sampled_cells


def make_folds(sub, n_folds=config.CV_FOLDS):
    """Reproduce the exact step-05 5 km GroupKFold splits on the subsample."""
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


def partial_dependence_1d(gam, term_index, X_eval):
    """Return 1-D partial dependence values for a single term."""
    s_effect = gam.partial_dependence(term=term_index, X=X_eval)
    return np.asarray(s_effect).ravel()


def derivative_zero_crossings(gam, x_min, x_max, n_points=500):
    """Find local extrema (first-derivative zero crossings) of s(built)."""
    xs = np.linspace(x_min, x_max, n_points)
    # ndvi = 0 (arbitrary reference, additive model), year = 0
    X_eval = np.column_stack([xs, np.zeros(n_points), np.zeros(n_points)])
    # Use finite differences on the partial dependence of term 0
    pd_vals = partial_dependence_1d(gam, 0, X_eval)
    # First derivative via central difference
    dx = xs[1] - xs[0]
    deriv = np.gradient(pd_vals, dx)
    # Second derivative to classify extrema
    second = np.gradient(deriv, dx)
    crossings = []
    for i in range(1, len(deriv) - 1):
        if deriv[i - 1] < 0 < deriv[i] or deriv[i - 1] > 0 > deriv[i]:
            xc = xs[i]
            xtype = "min" if second[i] > 0 else "max"
            crossings.append({"type": xtype, "built": float(xc)})
    return crossings


def bootstrap_predictions(gam_terms, X, y, groups, X_eval, lam, n_draws, seed):
    """200-draw 5 km block bootstrap: resample blocks, refit, predict."""
    rng = np.random.default_rng(seed)
    unique_blocks = np.unique(groups)
    n_blocks = len(unique_blocks)
    block_to_idx = {b: np.where(groups == b)[0] for b in unique_blocks}
    draws = np.full((n_draws, len(X_eval)), np.nan)
    for draw in range(n_draws):
        drawn = rng.choice(unique_blocks, size=n_blocks, replace=True)
        train_idx = np.concatenate([block_to_idx[b] for b in drawn])
        fold = LinearGAM(gam_terms, lam=lam)
        fold.fit(X[train_idx], y[train_idx])
        draws[draw, :] = fold.predict(X_eval)
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

    # --- Exact step-05 subsample and folds ---
    sub, sampled_cells = subsample_panel(panel, seed=SEED)
    year_levels = sorted(int(year) for year in sub["year"].unique())
    sub["year_code"] = sub["year"].map(
        {year: code for code, year in enumerate(year_levels)}
    )
    X = sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
    y = sub["lst_rel"].to_numpy(dtype=float)
    groups = block_key_from_xy(sub["x"].to_numpy(), sub["y"].to_numpy())
    splits = make_folds(sub, n_folds=config.CV_FOLDS)

    city_median_ndvi = float(panel["ndvi"].median())

    # ===== Part A: Within-context smooths (H6) =====
    sub["class_group"] = sub["ladder_class"].map(CLASS_MAP)

    coverage = []
    context_results = []
    csv_rows = []

    for code in range(len(CLASS_ORDER)):
        label = CLASS_LABELS[code]
        ctx_sub = sub[sub["class_group"] == code].copy()
        n_cells = int(ctx_sub["grid_id"].nunique())
        ctx_blocks = block_key_from_xy(
            ctx_sub["x"].to_numpy(), ctx_sub["y"].to_numpy()
        )
        n_blocks = int(len(np.unique(ctx_blocks)))
        q01 = float(ctx_sub["built"].quantile(0.01))
        q99 = float(ctx_sub["built"].quantile(0.99))

        coverage.append(
            {
                "context": label,
                "n_cells": n_cells,
                "n_blocks": n_blocks,
                "built_q05": q01,
                "built_q099": q99,
                "eligible": bool(n_cells >= MIN_CELLS and n_blocks >= MIN_BLOCKS),
            }
        )

        if n_cells < MIN_CELLS or n_blocks < MIN_BLOCKS:
            context_results.append(
                {
                    "context": label,
                    "eligible": False,
                    "reason": f"cells={n_cells} blocks={n_blocks}",
                }
            )
            continue

        # Fit within-context GAM: lst_rel ~ s(built) + s(ndvi) + f(year)
        X_ctx = ctx_sub[["built", "ndvi", "year_code"]].to_numpy(dtype=float)
        y_ctx = ctx_sub["lst_rel"].to_numpy(dtype=float)
        groups_ctx = block_key_from_xy(
            ctx_sub["x"].to_numpy(), ctx_sub["y"].to_numpy()
        )

        gam = LinearGAM(s(0) + s(1) + f(2))
        gam.gridsearch(X_ctx, y_ctx, lam=LAM_GRID, progress=False)
        selected_lam = flat_lam(gam.lam)

        # Evaluation grid: built from q01 to q99, ndvi = city median, year = 2022 (code 0)
        year_2022_code = year_levels.index(2022) if 2022 in year_levels else 0
        built_eval = np.linspace(q01, q99, N_EVAL_POINTS)
        X_eval = np.column_stack(
            [
                built_eval,
                np.full(N_EVAL_POINTS, city_median_ndvi),
                np.full(N_EVAL_POINTS, float(year_2022_code)),
            ]
        )

        # Point predictions
        gam_full = LinearGAM(s(0) + s(1) + f(2), lam=selected_lam)
        gam_full.fit(X_ctx, y_ctx)
        pred = gam_full.predict(X_eval)

        # Bootstrap CIs — pass the full lam array (one per term) as selected by gridsearch
        groups_eval_ctx = groups_ctx
        ci_low, ci_high = bootstrap_predictions(
            s(0) + s(1) + f(2),
            X_ctx,
            y_ctx,
            groups_eval_ctx,
            X_eval,
            gam.lam,
            N_BOOTSTRAP,
            BOOTSTRAP_SEED,
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

    # ===== Part B: Formal nonlinearity check (H2) =====
    # Same subsample, same folds as step 05
    # Linear: built + s(ndvi) + f(year)
    # Nonlinear: s(built) + s(ndvi) + f(year)

    linear_terms = X  # built is column 0, used linearly via s(0) with many basis? No — use linear term
    # In pygam, a linear term is just s(0, n_splines=1, order=1) or we can pass the raw column
    # pygam LinearGAM expects smooth terms; for a purely linear term use s(0, order=1)
    from pygam import s as _s

    linear_terms_pygam = _s(0, spline_order=1) + _s(1) + f(2)
    nonlinear_terms_pygam = _s(0) + _s(1) + f(2)

    # Gridsearch lam for each on the full subsample
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

    # Derivative zero crossings of s(built) from nonlinear model
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
    }
    with open(output_dir / "rq2_context.json", "w") as handle:
        json.dump(result, handle, indent=2)

    # Figure 5: class-specific partial built-up curves
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
