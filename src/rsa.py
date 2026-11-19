from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr


def correlation_rdm(features: np.ndarray) -> np.ndarray:
    if features.ndim != 2 or features.shape[0] < 3:
        raise ValueError("Features must be [images, features] with at least 3 images.")
    if not np.isfinite(features).all():
        raise ValueError("Features contain NaN or infinity.")
    rdm = squareform(pdist(features, metric="correlation"))
    return np.nan_to_num(rdm, nan=0.0, posinf=1.0, neginf=0.0)


def rsa_spearman(first: np.ndarray, second: np.ndarray) -> float:
    if first.shape != second.shape:
        raise ValueError("RDM dimensions differ.")
    upper = np.triu_indices(first.shape[0], k=1)
    value = spearmanr(first[upper], second[upper]).statistic
    return float(value) if np.isfinite(value) else 0.0


