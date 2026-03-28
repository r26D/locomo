#!/usr/bin/env bash
# Quick sanity check: small QA subset + one model. Does not use RAG embeddings.
#
# Usage (host venv):
#   bash scripts/smoke_eval_qa.sh
#
# Docker:
#   task docker:run -- bash scripts/smoke_eval_qa.sh
#
# Env overrides:
#   SMOKE_MAX_QUESTIONS=50   — passed to slice_locomo_qa.py
#   SMOKE_MAX_SAMPLES=2    — optional cap on conversations (see slice script)
#   SMOKE_MODEL=gpt-3.5-turbo
#   SMOKE_DATA=./data/locomo10_smoke_50qa.json
#   QA_OUTPUT_FILE=locomo10_smoke_qa.json  — from env.sh; use a unique name vs full runs

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
# shellcheck source=scripts/env.sh
source "$SCRIPT_DIR/env.sh"

SMOKE_MAX_QUESTIONS="${SMOKE_MAX_QUESTIONS:-50}"
SMOKE_DATA="${SMOKE_DATA:-$LOCOMO_ROOT/data/locomo10_smoke_${SMOKE_MAX_QUESTIONS}qa.json}"
SMOKE_MODEL="${SMOKE_MODEL:-gpt-3.5-turbo}"

SLICE_ARGS=(--input "$LOCOMO_ROOT/data/locomo10.json" --output "$SMOKE_DATA" --max-questions "$SMOKE_MAX_QUESTIONS" --overwrite)
if [ -n "${SMOKE_MAX_SAMPLES:-}" ]; then
  SLICE_ARGS+=(--max-samples "$SMOKE_MAX_SAMPLES")
fi

"$LOCOMO_PYTHON" "$SCRIPT_DIR/slice_locomo_qa.py" "${SLICE_ARGS[@]}"

mkdir -p "$OUT_DIR"

export DATA_FILE_PATH="$SMOKE_DATA"
export QA_OUTPUT_FILE="${QA_OUTPUT_FILE:-locomo10_smoke_qa.json}"

echo "Running evaluate_qa: model=$SMOKE_MODEL data=$DATA_FILE_PATH out=$OUT_DIR/$QA_OUTPUT_FILE"
"$LOCOMO_PYTHON" task_eval/evaluate_qa.py \
  --data-file "$DATA_FILE_PATH" \
  --out-file "$OUT_DIR/$QA_OUTPUT_FILE" \
  --model "$SMOKE_MODEL" \
  --batch-size 10

echo "Done. Predictions: $OUT_DIR/$QA_OUTPUT_FILE"
echo "Stats: ${OUT_DIR}/${QA_OUTPUT_FILE%.json}_stats.json"
