from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import (EEG_TMAX, EEG_TMIN, FLYVIS_DT, FLYVIS_FRAMES, N_IMAGES,
                    PERMUTATIONS, RANDOM_SEED, RESULTS_DIR)
from src.environment import diagnose


def main() -> None:
    parser = argparse.ArgumentParser(description="Exploratory FlyVis–THINGS-EEG2 image-level RSA")
    parser.add_argument("--images", type=int, default=N_IMAGES, help="Number of test images (minimum 3)")
    parser.add_argument("--permutations", type=int, default=PERMUTATIONS)
    parser.add_argument("--train-mapper", action="store_true",
                        help="Train and image-level cross-validate FlyVis-to-EEG kernel ridge mapping (needs >=20 images)")
    args = parser.parse_args()
    if args.images < 3:
        parser.error("--images must be >= 3")
    if args.train_mapper and args.images < 20:
        parser.error("--train-mapper needs --images >= 20; use >=100 for a more useful first pilot.")
    diagnose()
    # Import the heavier analysis modules only after the environment check gives actionable feedback.
    import numpy as np
    import pandas as pd
    from src.data_access import load_dataset_subset
    from src.cross_species_model import train_and_evaluate
    from src.eeg_loader import extract_eeg_features
    from src.flyvis_loader import extract_flyvis_features
    from src.rsa import correlation_rdm
    from src.permutation_test import image_permutation_test
    from src.stimulus import load_gray, normalize_image_id, resolve_stimulus_map
    from src.visualization import save_rdm_figure
    events, stimuli, images_root = load_dataset_subset()
    image_map = resolve_stimulus_map(stimuli, images_root)
    events["img_id"] = events["img_id"].map(normalize_image_id)
    valid_ids = [value for value in events["img_id"].dropna().unique() if value in image_map]
    selected_ids = valid_ids[:args.images]
    if len(selected_ids) < 3:
        raise RuntimeError(f"Only {len(selected_ids)} test events map to actual stimulus files; refusing RSA.")
    print(f"Mapped {len(selected_ids)} verified image IDs: {selected_ids}")
    images = [load_gray(image_map[image_id]) for image_id in selected_ids]
    eeg_ids, eeg_features, trial_counts = extract_eeg_features(
        ROOT / "data" / "raw" / "sub-01_ses-01_task-test_eeg.bdf", events,
        selected_ids, EEG_TMIN, EEG_TMAX)
    id_to_index = {image_id: i for i, image_id in enumerate(selected_ids)}
    aligned_images = [images[id_to_index[image_id]] for image_id in eeg_ids]
    fly_features = extract_flyvis_features(aligned_images, FLYVIS_FRAMES, FLYVIS_DT)
    fly_rdm = correlation_rdm(fly_features)
    eeg_rdm = correlation_rdm(eeg_features)
    rho, p_perm = image_permutation_test(fly_rdm, eeg_rdm, args.permutations, RANDOM_SEED)

    feature_dir = RESULTS_DIR / "features"
    report_dir = RESULTS_DIR / "reports"
    figure_dir = RESULTS_DIR / "figures"
    for directory in (feature_dir, report_dir, figure_dir):
        directory.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(feature_dir / "exploratory_features.npz", image_ids=np.asarray(eeg_ids),
                        flyvis=fly_features, eeg=eeg_features, flyvis_rdm=fly_rdm, eeg_rdm=eeg_rdm)
    save_rdm_figure(fly_rdm, eeg_rdm, eeg_ids, figure_dir / "rdm_comparison.png")
    result = {
        "analysis": "exploratory cross-system RSA; not mental imagery decoding",
        "subject": "sub-01", "session": "ses-01", "image_ids": eeg_ids,
        "valid_eeg_trials_per_image": trial_counts, "flyvis_features_shape": list(fly_features.shape),
        "eeg_features_shape": list(eeg_features.shape), "spearman_rho": rho,
        "image_label_permutation_p_two_sided": p_perm, "permutations": args.permutations,
        "seed": RANDOM_SEED, "interpretation": "Exploratory only; a small image subset cannot support biological claims."
    }
    (report_dir / "rsa_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame({"image_id": eeg_ids, "EEG_trials": [trial_counts[k] for k in eeg_ids]}).to_csv(
        report_dir / "included_images.csv", index=False)
    if args.train_mapper:
        if len(eeg_ids) < 20:
            raise RuntimeError(f"Only {len(eeg_ids)} images have EEG features; mapper requires at least 20.")
        mapper_report, mapper_artifact = train_and_evaluate(
            fly_features, eeg_features, folds=5, alpha=1.0, seed=RANDOM_SEED)
        mapper_report["image_ids"] = eeg_ids
        (report_dir / "cross_species_mapper_cv.json").write_text(
            json.dumps(mapper_report, indent=2), encoding="utf-8")
        np.savez_compressed(feature_dir / "cross_species_mapper.npz",
                            image_ids=np.asarray(eeg_ids), **mapper_artifact)
        print("Cross-species mapper CV:")
        print(json.dumps(mapper_report, indent=2))
    print(json.dumps(result, indent=2))
    print(f"Saved results under {RESULTS_DIR}")


if __name__ == "__main__":
    main()
