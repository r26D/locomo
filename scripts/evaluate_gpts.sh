SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
# shellcheck source=scripts/env.sh
source "$SCRIPT_DIR/env.sh"

# Evaluate gpt-4-turbo
"$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
    --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$QA_OUTPUT_FILE \
    --model gpt-4-turbo --batch-size 20

# Evaluate gpt-3.5-turbo under different context lengths
for MODEL in gpt-3.5-turbo-4k gpt-3.5-turbo-8k gpt-3.5-turbo-12k gpt-3.5-turbo-16k; do
    "$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
        --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$QA_OUTPUT_FILE \
        --model $MODEL --batch-size 10
done
