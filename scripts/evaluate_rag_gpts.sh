SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
# shellcheck source=scripts/env.sh
source "$SCRIPT_DIR/env.sh"

# Evaluate gpt-3.5-turbo under different RAG conditions

# dialog as database
for TOP_K in 5 10 25 50; do
    "$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
        --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$QA_OUTPUT_FILE \
        --model gpt-3.5-turbo --batch-size 1 --use-rag --retriever dragon --top-k $TOP_K \
        --emb-dir $EMB_DIR --rag-mode dialog
done

# observation as database
for TOP_K in 5 10 25 50; do
    "$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
        --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$QA_OUTPUT_FILE \
        --model gpt-3.5-turbo --batch-size 1 --use-rag --retriever dragon --top-k $TOP_K \
        --emb-dir $EMB_DIR --rag-mode observation
done

# summary as database
for TOP_K in 2 5 10; do
    "$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
        --data-file $DATA_FILE_PATH --out-file $OUT_DIR/$QA_OUTPUT_FILE \
        --model gpt-3.5-turbo --batch-size 1 --use-rag --retriever dragon --top-k $TOP_K \
        --emb-dir $EMB_DIR --rag-mode summary
done
