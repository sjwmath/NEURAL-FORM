#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" - <<'PY'
import sys
if not ((3, 9) <= sys.version_info[:2] < (3, 13)):
    raise SystemExit(f"FlyVis needs Python 3.9–3.12; found {sys.version.split()[0]}")
PY
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON_BIN" -m venv .venv
fi
if [[ ! -f .venv/.neural_form_deps_ready ]]; then
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
  touch .venv/.neural_form_deps_ready
fi
if ! .venv/bin/python -c 'import flyvis, mne' >/dev/null 2>&1; then
  echo "Dependency import check failed. Re-run after reviewing the pip error above." >&2
  exit 1
fi
MODEL_PATH="$(.venv/bin/python -c 'import flyvis; print(flyvis.results_dir / "flow/0000/000")')"
if [[ ! -e "$MODEL_PATH" ]]; then
  .venv/bin/flyvis download-pretrained
fi
RUN_ARGS=(--images "${IMAGES:-5}" --permutations "${PERMUTATIONS:-999}")
if [[ "${TRAIN_MAPPER:-0}" == "1" ]]; then
  RUN_ARGS+=(--train-mapper)
fi
.venv/bin/python -m src.main "${RUN_ARGS[@]}"
