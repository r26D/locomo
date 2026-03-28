SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
# shellcheck source=scripts/env.sh
source "$SCRIPT_DIR/env.sh"

# Evaluate Gemini (default: current flash model; legacy gemini-pro-1.0 maps to API model in evaluate_qa.py)
"$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
    --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$QA_OUTPUT_FILE \
    --model gemini-2.5-flash --batch-size 20
