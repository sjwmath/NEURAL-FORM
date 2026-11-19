from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import requests

from config import BASE_URL, RAW_DIR, STIMULI_DIR, SUBJECT, SESSION
from src.stimulus import normalize_event_identifier


def _download(url: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        print(f"Cache hit: {target.name}")
        return target
    tmp = target.with_suffix(target.suffix + ".part")
    print(f"Downloading {url} ({target.name})")
    with requests.get(url, stream=True, timeout=(30, 180)) as response:
        response.raise_for_status()
        with tmp.open("wb") as out:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    out.write(chunk)
    tmp.replace(target)
    return target


def load_dataset_subset() -> tuple[pd.DataFrame, pd.DataFrame, Path]:
    """Fetch one official test recording, event table, stimulus map and small test image archive."""
    stem = f"sub-{SUBJECT}_ses-{SESSION}_task-test"
    eeg_path = _download(f"{BASE_URL}/sub-{SUBJECT}/ses-{SESSION}/eeg/{stem}_eeg.bdf", RAW_DIR / f"{stem}_eeg.bdf")
    events_path = _download(f"{BASE_URL}/sub-{SUBJECT}/ses-{SESSION}/eeg/{stem}_events.tsv", RAW_DIR / f"{stem}_events.tsv")
    stimuli_tsv = _download(f"{BASE_URL}/stimuli/stimuli.tsv", STIMULI_DIR / "stimuli.tsv")
    archive = _download(f"{BASE_URL}/stimuli/test_images.zip", STIMULI_DIR / "test_images.zip")
    images_root = STIMULI_DIR / "test_images"
    if not images_root.exists():
        images_root.mkdir(parents=True)
        with zipfile.ZipFile(archive) as zf:
            # Refuse archive traversal; extract only under the intended data folder.
            root = images_root.resolve()
            for member in zf.infolist():
                destination = (images_root / member.filename).resolve()
                if destination != root and root not in destination.parents:
                    raise RuntimeError(f"Unsafe path in stimulus archive: {member.filename}")
            zf.extractall(images_root)
    events = pd.read_csv(events_path, sep="\t")
    stimuli = pd.read_csv(stimuli_tsv, sep="\t")
    if "onset" not in events:
        raise RuntimeError(f"Expected onset in events.tsv; actual columns: {events.columns.tolist()}")
    # In the released test events, tot_img_number identifies the test-stimulus number.
    # Preserve it as a canonical BIDS stimulus key only after checking that the field exists.
    source_id = "img_id" if "img_id" in events.columns else "tot_img_number" if "tot_img_number" in events.columns else None
    if source_id is None:
        raise RuntimeError(f"No known stimulus identifier in events.tsv: {events.columns.tolist()}")
    events["img_id"] = events[source_id].map(normalize_event_identifier)
    return events, stimuli, images_root
