# LoCoMo image (locked deps via uv). Mount ./data and host outputs at runtime (e.g. external_outputs -> /app/outputs).
# python:3.12-slim-bookworm — aligns with .tool-versions. On Linux amd64, uv.lock may pull CUDA-capable PyTorch; use CPU without --gpus.
# uv pinned via PyPI to match .tool-versions (ARG UV_VERSION; not an unpinned :latest install).
#
# Build runs `uv sync --frozen` as user `locomo` so `.venv` is created with correct ownership. We avoid
# `chown -R /app` after install (that walked the whole venv and made builds look hung on large trees).
# Writable runtime dirs: use host mounts for `/app/outputs` and, when generating, a read-write `/app/data`.
FROM python:3.12-slim-bookworm

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Pin uv to match .tool-versions (PyPI package installs the `uv` CLI on PATH).
ARG UV_VERSION=0.11.2

# Pillow and other wheels may need runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv==${UV_VERSION}"

RUN useradd --create-home --shell /bin/bash --uid 10000 locomo \
    && mkdir -p /app \
    && chown locomo:locomo /app

WORKDIR /app

COPY --chown=locomo:locomo pyproject.toml uv.lock README.MD ./
COPY --chown=locomo:locomo global_methods.py device_utils.py ./
COPY --chown=locomo:locomo generative_agents/ ./generative_agents/
COPY --chown=locomo:locomo task_eval/ ./task_eval/
COPY --chown=locomo:locomo prompt_examples/ ./prompt_examples/
COPY --chown=locomo:locomo scripts/ ./scripts/

USER locomo
RUN uv sync --frozen

WORKDIR /app

CMD ["bash"]
