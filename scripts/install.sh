#!/usr/bin/env bash
set -euo pipefail
cd /workspace/IEEE-RAL
source scripts/env.sh
uv sync --frozen
uv run python -c 'import sapien, mujoco, torch; assert not torch.cuda.is_available(); print(sapien.__version__, mujoco.__version__, torch.__version__)'
