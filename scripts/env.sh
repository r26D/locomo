# Repository root (directory containing scripts/ and data/).
if [ -n "${BASH_SOURCE[0]-}" ]; then
  _LOCOMO_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  LOCOMO_ROOT="$(cd "$_LOCOMO_SCRIPTS/.." && pwd)"
else
  LOCOMO_ROOT="$(pwd)"
fi
export LOCOMO_ROOT

# Python: if unset, prefer project .venv, then asdf (.tool-versions). Pre-set LOCOMO_PYTHON (e.g. Docker) wins.
# Create venv: cd "$LOCOMO_ROOT" && asdf exec python -m venv .venv && .venv/bin/pip install -e .
if [ -z "${LOCOMO_PYTHON:-}" ]; then
  if [ -x "$LOCOMO_ROOT/.venv/bin/python" ]; then
    LOCOMO_PYTHON="$LOCOMO_ROOT/.venv/bin/python"
  elif command -v asdf >/dev/null 2>&1; then
    _asdf_py="$(cd "$LOCOMO_ROOT" && asdf which python 2>/dev/null)" || true
    if [ -z "$_asdf_py" ] || [ ! -x "$_asdf_py" ]; then
      _asdf_py="$(cd "$LOCOMO_ROOT" && asdf which python3 2>/dev/null)" || true
    fi
    if [ -n "$_asdf_py" ] && [ -x "$_asdf_py" ]; then
      LOCOMO_PYTHON="$_asdf_py"
    fi
  fi
fi
LOCOMO_PYTHON="${LOCOMO_PYTHON:-python3}"
export LOCOMO_PYTHON

# Paths — defaults for repo-root runs; honor pre-set values (Docker env_file, CI, etc.)
OUT_DIR="${OUT_DIR:-./outputs}"
EMB_DIR="${EMB_DIR:-./outputs}"
DATA_FILE_PATH="${DATA_FILE_PATH:-./data/locomo10.json}"
QA_OUTPUT_FILE="${QA_OUTPUT_FILE:-locomo10_qa.json}"
OBS_OUTPUT_FILE="${OBS_OUTPUT_FILE:-locomo10_observation.json}"
SESS_SUMM_OUTPUT_FILE="${SESS_SUMM_OUTPUT_FILE:-locomo10_session_summary.json}"
PROMPT_DIR="${PROMPT_DIR:-./prompt_examples}"
export OUT_DIR EMB_DIR DATA_FILE_PATH QA_OUTPUT_FILE OBS_OUTPUT_FILE SESS_SUMM_OUTPUT_FILE PROMPT_DIR

# API keys — do not overwrite values injected by the environment
export LOCOMO_OPENAI_API_KEY="${LOCOMO_OPENAI_API_KEY:-}"

# Optional OpenAI model overrides (modern SDK; defaults are small/cheap models)
# export LOCOMO_OPENAI_CHAT_MODEL=gpt-4o-mini          # used when code passes model alias "chatgpt"
# export LOCOMO_OPENAI_CHAT_MODEL_16K=gpt-4o-mini      # used with use_16k in few-shot helpers
# export LOCOMO_OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Optional Anthropic defaults when using short names claude-sonnet / claude-haiku in scripts
# export LOCOMO_CLAUDE_SONNET_MODEL=claude-3-5-sonnet-20241022
# export LOCOMO_CLAUDE_HAIKU_MODEL=claude-3-5-haiku-20241022

# BLIP image captions (--blip-caption): outputs can differ slightly across CUDA vs Apple MPS vs CPU.
# Omit --blip-caption for maximum cross-machine consistency when images are not required.

# Google API key for Gemini via the `google-genai` SDK (project-specific).
# Also accepted if unset: GOOGLE_API_KEY or GEMINI_API_KEY.
export LOCOMO_GOOGLE_API_KEY="${LOCOMO_GOOGLE_API_KEY:-}"

# Anthropic API Key (project-specific)
export LOCOMO_ANTHROPIC_API_KEY="${LOCOMO_ANTHROPIC_API_KEY:-}"

# HuggingFace Token (project-specific)
export LOCOMO_HF_TOKEN="${LOCOMO_HF_TOKEN:-}"
