from __future__ import annotations

import importlib.util
import platform
import sys


def diagnose() -> None:
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"OS: {platform.platform()}")
    if sys.version_info < (3, 9) or sys.version_info >= (3, 13):
        raise RuntimeError("FlyVis requires Python >=3.9,<3.13. Use Python 3.9–3.12.")
    if platform.system() == "Windows":
        print("NOTE: FlyVis documentation reports Linux testing; native Windows support is not guaranteed.")
    missing = [name for name in ("flyvis", "torch", "mne", "numpy", "pandas", "scipy", "matplotlib", "PIL")
               if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError("Missing packages: " + ", ".join(missing) + ". Run .\\run.ps1 -Install or follow README.md.")
    import torch
    print(f"PyTorch: {torch.__version__}; CUDA available: {torch.cuda.is_available()}")
    import flyvis
    print(f"FlyVis import OK: {getattr(flyvis, '__version__', 'version not exposed')}")
