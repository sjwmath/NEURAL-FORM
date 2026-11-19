from __future__ import annotations

from pathlib import Path

import mne
import numpy as np
import pandas as pd
from src.feature_extraction import reduce_eeg_epochs
from src.preprocessing import prepare_eeg_raw
from src.stimulus import normalize_image_id


def extract_eeg_features(eeg_path: Path, events: pd.DataFrame, selected_ids: list[str],
                         tmin: float, tmax: float) -> tuple[list[str], np.ndarray, dict[str, int]]:
    """Epoch the BDF recording at BIDS event onsets; average repeats by canonical stimulus ID."""
    raw = mne.io.read_raw_bdf(eeg_path, preload=True, verbose="ERROR")
    raw = prepare_eeg_raw(raw)
    sfreq = float(raw.info["sfreq"])
    rows = events.copy()
    rows["img_id"] = rows["img_id"].map(normalize_image_id)
    rows = rows[rows["img_id"].isin(selected_ids)].copy()
    if rows.empty:
        raise RuntimeError("No events remained after matching selected image IDs.")
    # BIDS onset is seconds from recording start. Explicit event arrays avoid relying on BDF trigger coding.
    onset_samples = np.round(pd.to_numeric(rows["onset"], errors="raise").to_numpy() * sfreq).astype(int) + raw.first_samp
    event_array = np.column_stack([onset_samples, np.zeros(len(rows), dtype=int), np.ones(len(rows), dtype=int)])
    epochs = mne.Epochs(raw, event_array, event_id={"image": 1}, tmin=tmin, tmax=tmax,
                        baseline=None, preload=True, reject_by_annotation=True, verbose="ERROR")
    data = epochs.get_data(copy=True)  # trials × EEG channels × time
    if len(data) != len(rows):
        # MNE may drop epochs that overlap annotated bad segments; use its retained indices.
        rows = rows.iloc[epochs.selection].copy()
    # A compact, transparent feature: channel-wise means over the selected visual-response window.
    trial_features = reduce_eeg_epochs(data)
    by_id: dict[str, list[np.ndarray]] = {}
    for image_id, vector in zip(rows["img_id"].tolist(), trial_features):
        by_id.setdefault(image_id, []).append(vector)
    kept = [image_id for image_id in selected_ids if image_id in by_id]
    if len(kept) < 3:
        raise RuntimeError(f"Only {len(kept)} images have valid EEG epochs; need at least 3 for exploratory RSA.")
    features = np.stack([np.mean(by_id[image_id], axis=0) for image_id in kept])
    return kept, features.astype(np.float32), {k: len(by_id[k]) for k in kept}
