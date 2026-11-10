# Source from any directory; defaults are local to this checkout.
DUAL_REC_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export DUAL_REC_ROOT
export UV_CACHE_DIR="${UV_CACHE_DIR:-${DUAL_REC_ROOT}/.cache/uv}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-${DUAL_REC_ROOT}/.cache/matplotlib}"
export NUMBA_CACHE_DIR="${NUMBA_CACHE_DIR:-${DUAL_REC_ROOT}/.cache/numba}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${DUAL_REC_ROOT}/.cache}"
export MUJOCO_GL="${MUJOCO_GL:-egl}"
# This bounded qualification must not inherit a larger numerical-thread budget.
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export CC="${CC:-gcc}"
