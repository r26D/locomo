#!/usr/bin/env bash
# Run a command in the LoCoMo image with repo data and host outputs mounted.
# Data is mounted read-only here; generation flows that write under data/ (multimodal_dialog/, msc_personas_all.json)
# need a read-write mount—use `task docker:run-data-rw` or adjust the -v data line.
# Usage: scripts/docker-run.sh bash scripts/evaluate_gpts.sh
#
# Optional environment (host):
#   LOCOMO_DOCKER_IMAGE   image name (default: locomo:local)
#   LOCOMO_DOCKER_ENV_FILE  secrets file path (default: repo/.env.docker)
#   LOCOMO_DOCKER_USER    override container user (default: host $(id -u):$(id -g) for bind mounts)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

IMAGE="${LOCOMO_DOCKER_IMAGE:-locomo:local}"
ENV_FILE="${LOCOMO_DOCKER_ENV_FILE:-$ROOT/.env.docker}"

if [ ! -f "$ENV_FILE" ]; then
  if [ "$ENV_FILE" = "$ROOT/.env.docker" ]; then
    cp "$ROOT/env.docker.example" "$ENV_FILE"
  else
    echo "Missing env file: $ENV_FILE" >&2
    exit 1
  fi
fi

if ! docker image inspect "$IMAGE" &>/dev/null; then
  docker build -t "$IMAGE" "$ROOT"
fi

# Match host UID/GID so ./external_outputs and (if rw) ./data are writable without root-owned files.
RUN_USER="${LOCOMO_DOCKER_USER:-$(id -u):$(id -g)}"

exec docker run --rm --user "$RUN_USER" -w /app \
  -v "$ROOT/data:/app/data:ro" \
  -v "$ROOT/external_outputs:/app/outputs" \
  --env-file "$ENV_FILE" \
  "$IMAGE" "$@"
