"""Image-level FlyVis-to-EEG mapping using leakage-safe linear kernel ridge regression."""

from __future__ import annotations

import numpy as np


def _fit_kernel(train_x: np.ndarray, train_y: np.ndarray, alpha: float) -> tuple[np.ndarray, ...]:
    x_mean = train_x.mean(axis=0, dtype=np.float64).astype(np.float32)
    x_scale = train_x.std(axis=0, dtype=np.float64).astype(np.float32)
    x_scale[x_scale < 1e-8] = 1.0
    x = (train_x - x_mean) / x_scale
    y_mean = train_y.mean(axis=0, dtype=np.float64).astype(np.float32)
    y_scale = train_y.std(axis=0, dtype=np.float64).astype(np.float32)
    y_scale[y_scale < 1e-8] = 1.0
    y = (train_y - y_mean) / y_scale
    kernel = (x @ x.T) / max(x.shape[1], 1)
    dual = np.linalg.solve(kernel + alpha * np.eye(len(kernel), dtype=np.float32), y)
    return x_mean, x_scale, y_mean, y_scale, x, dual


def _predict(x_new: np.ndarray, fitted: tuple[np.ndarray, ...]) -> np.ndarray:
    x_mean, x_scale, y_mean, y_scale, x_train, dual = fitted
    x = (x_new - x_mean) / x_scale
    kernel = (x @ x_train.T) / max(x.shape[1], 1)
    return (kernel @ dual) * y_scale + y_mean


def predict_eeg_features(flyvis_features: np.ndarray, artifact: dict[str, np.ndarray]) -> np.ndarray:
    """Predict EEG feature vectors from new FlyVis feature rows using the exported final model."""
    required = {"train_x_mean", "train_x_scale", "train_y_mean", "train_y_scale",
                "scaled_train_x", "dual_coefficients"}
    missing = required.difference(artifact)
    if missing:
        raise ValueError(f"Mapper artifact is missing fields: {sorted(missing)}")
    fitted = tuple(artifact[key] for key in (
        "train_x_mean", "train_x_scale", "train_y_mean", "train_y_scale",
        "scaled_train_x", "dual_coefficients"))
    x_new = np.asarray(flyvis_features, dtype=np.float32)
    if x_new.ndim != 2 or x_new.shape[1] != len(fitted[0]):
        raise ValueError(f"Expected FlyVis features with {len(fitted[0])} columns; got {x_new.shape}.")
    return _predict(x_new, fitted)


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    correlations = []
    r2_values = []
    for channel in range(actual.shape[1]):
        a = actual[:, channel].astype(np.float64)
        p = predicted[:, channel].astype(np.float64)
        if np.std(a) > 0 and np.std(p) > 0:
            correlations.append(float(np.corrcoef(a, p)[0, 1]))
        total = np.sum((a - np.mean(a)) ** 2)
        r2_values.append(float(1 - np.sum((a - p) ** 2) / total) if total > 0 else 0.0)
    return {
        "mean_channel_pearson_r": float(np.mean(correlations)) if correlations else 0.0,
        "mean_channel_r2": float(np.mean(r2_values)) if r2_values else 0.0,
        "mean_squared_error": float(np.mean((actual - predicted) ** 2)),
    }


def train_and_evaluate(flyvis_features: np.ndarray, eeg_features: np.ndarray,
                       folds: int = 5, alpha: float = 1.0, seed: int = 42
                       ) -> tuple[dict, dict[str, np.ndarray]]:
    """Cross-validate by image ID, then fit a final export model on all paired images."""
    x = np.asarray(flyvis_features, dtype=np.float32)
    y = np.asarray(eeg_features, dtype=np.float32)
    if x.ndim != 2 or y.ndim != 2 or len(x) != len(y):
        raise ValueError("FlyVis and EEG features must be 2-D arrays with the same image count.")
    if len(x) < max(20, folds * 4):
        raise ValueError(f"Need at least {max(20, folds * 4)} paired images; got {len(x)}.")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Training features contain NaN or infinity.")
    if alpha <= 0:
        raise ValueError("alpha must be positive.")

    rng = np.random.default_rng(seed)
    validation_folds = np.array_split(rng.permutation(len(x)), folds)
    cv_prediction = np.full_like(y, np.nan, dtype=np.float32)
    fold_sizes = []
    all_indices = np.arange(len(x))
    for test_indices in validation_folds:
        train_indices = np.setdiff1d(all_indices, test_indices, assume_unique=True)
        fitted = _fit_kernel(x[train_indices], y[train_indices], alpha)
        cv_prediction[test_indices] = _predict(x[test_indices], fitted)
        fold_sizes.append({"train_images": int(len(train_indices)), "heldout_images": int(len(test_indices))})
    if not np.isfinite(cv_prediction).all():
        raise RuntimeError("Cross-validation did not produce a prediction for every image.")

    # Fold-wise training means form a transparent no-image-information baseline.
    baseline = np.zeros_like(y)
    for test_indices, fold_info in zip(validation_folds, fold_sizes):
        train_indices = np.setdiff1d(all_indices, test_indices, assume_unique=True)
        baseline[test_indices] = y[train_indices].mean(axis=0)

    final_model = _fit_kernel(x, y, alpha)
    metadata = {
        "model": "linear kernel ridge regression",
        "direction": "FlyVis response features -> human EEG response features",
        "validation": "5-fold image-level cross-validation; repeated EEG trials averaged before splitting",
        "n_images": int(len(x)),
        "flyvis_dimensions": int(x.shape[1]),
        "eeg_dimensions": int(y.shape[1]),
        "alpha": float(alpha),
        "seed": int(seed),
        "folds": fold_sizes,
        "cross_validated": _metrics(y, cv_prediction),
        "mean_baseline": _metrics(y, baseline),
        "interpretation": "Exploratory mapping of viewed-image responses, not mental-imagery decoding.",
    }
    artifact = {
        "image_level_cv_predictions": cv_prediction,
        "actual_eeg_features": y,
        "baseline_predictions": baseline,
        "train_x_mean": final_model[0],
        "train_x_scale": final_model[1],
        "train_y_mean": final_model[2],
        "train_y_scale": final_model[3],
        "scaled_train_x": final_model[4],
        "dual_coefficients": final_model[5],
    }
    return metadata, artifact
