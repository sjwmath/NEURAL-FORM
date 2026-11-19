"""Feature reductions used by the first exploratory run."""

import numpy as np


def reduce_flyvis_activity(activity, frames: int) -> np.ndarray:
    activity = np.asarray(activity)
    if activity.ndim != 3 or activity.shape[0] != 1:
        raise RuntimeError(f"Unexpected FlyVis output shape {activity.shape}; expected [1,T,cells].")
    return np.nanmean(activity[0, max(frames // 2, 0):], axis=0).astype(np.float32)


def reduce_eeg_epochs(epoch_data: np.ndarray) -> np.ndarray:
    """Return one channel vector per trial by averaging the selected time window."""
    values = np.nan_to_num(epoch_data, nan=0.0, posinf=0.0, neginf=0.0)
    return values.mean(axis=-1).astype(np.float32)
