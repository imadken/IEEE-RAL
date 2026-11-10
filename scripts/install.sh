#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source scripts/env.sh
command -v uv >/dev/null || { echo 'Install uv from https://docs.astral.sh/uv/getting-started/installation/'; exit 1; }
uv sync --frozen
uv run python -c 'import sapien, mujoco, torch; print(sapien.__version__, mujoco.__version__, torch.__version__)'
