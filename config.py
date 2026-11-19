"""Small, reproducible defaults for the first exploratory run."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STIMULI_DIR = DATA_DIR / "stimuli"
RESULTS_DIR = ROOT / "results"
SUBJECT = "01"
SESSION = "01"
N_IMAGES = 5
EEG_TMIN = 0.05
EEG_TMAX = 0.18
FLYVIS_DT = 0.01
FLYVIS_FRAMES = 20
PERMUTATIONS = 999
RANDOM_SEED = 42
BASE_URL = "https://data.nemar.org/nm000232/v1.1.1"
