SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
# shellcheck source=scripts/env.sh
source "$SCRIPT_DIR/env.sh"

"$LOCOMO_PYTHON" generative_agents/generate_conversations.py \
    --out-dir ./data/multimodal_dialog/example/ \
    --prompt-dir ./prompt_examples \
    --events --session --summary --num-sessions 3 \
    --persona \
    --num-days 90 --num-events 10 --max-turns-per-session 20 --num-events-per-session 1
