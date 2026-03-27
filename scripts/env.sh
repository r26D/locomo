# save generated outputs to this location
OUT_DIR=./outputs

# save embeddings to this location
EMB_DIR=./outputs

# path to LoCoMo data file
DATA_FILE_PATH=./data/locomo10.json

# filenames for different outputs
QA_OUTPUT_FILE=locomo10_qa.json
OBS_OUTPUT_FILE=locomo10_observation.json
SESS_SUMM_OUTPUT_FILE=locomo10_session_summary.json

# path to folder containing prompts and in-context examples
PROMPT_DIR=./prompt_examples

# OpenAI API Key (project-specific; avoids clashing with a global OPENAI_API_KEY)
export LOCOMO_OPENAI_API_KEY=

# Optional OpenAI model overrides (modern SDK; defaults are small/cheap models)
# export LOCOMO_OPENAI_CHAT_MODEL=gpt-4o-mini          # used when code passes model alias "chatgpt"
# export LOCOMO_OPENAI_CHAT_MODEL_16K=gpt-4o-mini      # used with use_16k in few-shot helpers
# export LOCOMO_OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Optional Anthropic defaults when using short names claude-sonnet / claude-haiku in scripts
# export LOCOMO_CLAUDE_SONNET_MODEL=claude-3-5-sonnet-20241022
# export LOCOMO_CLAUDE_HAIKU_MODEL=claude-3-5-haiku-20241022

# BLIP image captions (--blip-caption): outputs can differ slightly across CUDA vs Apple MPS vs CPU.
# Omit --blip-caption for maximum cross-machine consistency when images are not required.

# Google API Key
export GOOGLE_API_KEY=

# Anthropic API Key
export ANTHROPIC_API_KEY=

# HuggingFace Token
export HF_TOKEN=
