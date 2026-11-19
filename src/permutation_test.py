"""Image-label permutation test for two representational dissimilarity matrices."""

import numpy as np

from src.rsa import rsa_spearman


def image_permutation_test(first: np.ndarray, second: np.ndarray, n_perm: int, seed: int) -> tuple[float, float]:
    """Permute image labels (not the non-independent RDM edges)."""
    observed = rsa_spearman(first, second)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        order = rng.permutation(second.shape[0])
        permuted = second[np.ix_(order, order)]
        count += abs(rsa_spearman(first, permuted)) >= abs(observed)
    return observed, (count + 1) / (n_perm + 1)
