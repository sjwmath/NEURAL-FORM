from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def save_rdm_figure(flyvis_rdm: np.ndarray, eeg_rdm: np.ndarray, labels: list[str], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for ax, matrix, title in zip(axes, (flyvis_rdm, eeg_rdm), ("FlyVis model response", "Human EEG response")):
        image = ax.imshow(matrix, cmap="viridis")
        ax.set_title(title)
        ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=7)
        ax.set_yticks(range(len(labels)), labels, fontsize=7)
        fig.colorbar(image, ax=ax, shrink=.75, label="Correlation distance")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
