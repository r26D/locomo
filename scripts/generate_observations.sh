SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
# shellcheck source=scripts/env.sh
source "$SCRIPT_DIR/env.sh"

# gets observations using gpt-3.5-turbo and extract DRAGON embeddings for RAG database
"$LOCOMO_PYTHON" task_eval/get_facts.py --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$OBS_OUTPUT_FILE \
    --prompt-dir $PROMPT_DIR --emb-dir $EMB_DIR --use-date --overwrite