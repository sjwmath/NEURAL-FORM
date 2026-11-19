from __future__ import annotations

import numpy as np
import torch
from src.feature_extraction import reduce_flyvis_activity


def extract_flyvis_features(image_arrays: list[np.ndarray], frames: int, dt: float) -> np.ndarray:
    """Run the documented pretrained flow network on repeated static image exposures."""
    import flyvis
    from flyvis.datasets.rendering import BoxEye

    # Official FlyVis custom-stimuli example: BoxEye -> rendered receptors -> movie input.
    receptor = BoxEye(extent=15, kernel_size=13)
    model_path = flyvis.results_dir / "flow/0000/000"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Pretrained FlyVis model not found at {model_path}. Run `flyvis download-pretrained` once."
        )
    network = flyvis.NetworkView(model_path).init_network()
    device = torch.device("cpu")
    network.to(device)
    all_features: list[np.ndarray] = []
    for image in image_arrays:
        frame = torch.as_tensor(image, dtype=torch.float32, device=device)[None, None]
        # Official BoxEye input is [samples, frames, height, width].
        rendered = torch.as_tensor(receptor(frame), dtype=torch.float32, device=device)
        if rendered.ndim != 4 or rendered.shape[0] != 1:
            raise RuntimeError(f"Unexpected BoxEye output shape {tuple(rendered.shape)}; expected [1,1,1,721].")
        movie_input = rendered[0].repeat(frames, 1, 1)
        # The documented custom-stimulus API uses a batched [B,T,C] movie and a fade-in state.
        initial_state = network.fade_in_state(1.0, dt, movie_input[[0]])
        with torch.no_grad():
            activity = network.simulate(movie_input[None], dt, initial_state=initial_state)
        activity = torch.as_tensor(activity).detach().cpu().numpy()
        # Average the latter half of this repeated static exposure for one feature per image.
        all_features.append(reduce_flyvis_activity(activity, frames))
    return np.stack(all_features)
