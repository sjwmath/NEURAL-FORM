from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


def normalize_image_id(value: object) -> str:
    text = str(value).strip().lower().replace("\\", "/")
    stem = Path(text).stem
    return stem[:-2] if stem.endswith(".0") and stem[:-2].isdigit() else stem


def normalize_event_identifier(value: object) -> str:
    """Map THINGS-EEG2 test tot_img_number values to their documented stim-test IDs."""
    text = normalize_image_id(value)
    if text.isdigit():
        return f"stim-test{int(text):05d}"
    return text


def resolve_stimulus_map(stimuli: pd.DataFrame, images_root: Path) -> dict[str, Path]:
    """Resolve test IDs using the published stimuli table and exact local filenames."""
    files = [p for p in images_root.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}]
    by_stem: dict[str, Path] = {}
    for path in files:
        stem = normalize_image_id(path.name)
        by_stem.setdefault(stem, path)
        if stem.endswith("_image"):
            by_stem.setdefault(stem[:-6], path)
    id_cols = [c for c in stimuli.columns if c.lower() in {"img_id", "image_id", "stim_id", "stimulus_id", "trial_type"}]
    file_cols = [c for c in stimuli.columns if c.lower() in {"stim_file", "filename", "file_name", "image", "path"}]
    if not id_cols or not file_cols:
        raise RuntimeError(
            "Cannot establish exact image mapping from stimuli.tsv. "
            f"Columns found: {stimuli.columns.tolist()}. No RSA will be run until mapping is verified."
        )
    id_col, file_col = id_cols[0], file_cols[0]
    mapping: dict[str, Path] = {}
    for _, row in stimuli.iterrows():
        key = normalize_event_identifier(row[id_col])
        candidate = normalize_image_id(row[file_col])
        if candidate in by_stem:
            mapping[key] = by_stem[candidate]
    if not mapping:
        raise RuntimeError(f"No stimuli.tsv entries matched image filenames. ID={id_col}, file={file_col}; sample={stimuli[[id_col, file_col]].head().to_dict('records')}")
    return mapping


def load_gray(path: Path, size: int = 64) -> np.ndarray:
    """Load an image as float32 luminance in [0, 1]; do not crop to semantic content."""
    image = Image.open(path).convert("L").resize((size, size), Image.Resampling.BILINEAR)
    return np.asarray(image, dtype=np.float32) / 255.0
