# LoCoMo benchmark prep (before an external memory system)

This repo ships the **annotated benchmark** in `data/locomo10.json` (10 long conversations, **~1,986** QA items — often rounded to “~1.5k” in conversation). You do **not** need to regenerate those conversations to run the official QA task.

Your external memory project will replace how “context” is retrieved; this document gets **this** repo healthy end-to-end so integration is mostly “swap the retriever,” not “debug paths for six hours.”

## 1. What “base data” means here

| Goal | What you use | Notes |
|------|----------------|-------|
| Official QA benchmark | `data/locomo10.json` | Already in git. `conversation`, `qa`, `event_summary` fields, etc. |
| Optional: new synthetic dialogs | `scripts/generate_conversations.sh` | Needs **read-write** `data/` (Docker: `task docker:run-data-rw`). Separate from the released benchmark. |
| Built-in RAG baselines (this repo) | Observations + DRAGON embeddings, or session summaries, or dialog turns | Generated into `OUT_DIR` / `EMB_DIR` (see §4). Not required for full-context or external-memory tests. |

## 2. Environment and Docker (avoid the usual traps)

1. **API keys** — Set `LOCOMO_OPENAI_API_KEY` (and others only if you use those scripts). For Docker: `task docker:init` then edit `.env.docker`, or point `ENV_FILE` / `LOCOMO_COMPOSE_ENV_FILE` at a file **outside** the repo (`env.docker.example` explains this).

2. **Outputs directory** — `scripts/env.sh` defaults to `OUT_DIR=./outputs`. In the container, `./outputs` is the host folder `external_outputs/`. Create it once: `mkdir -p external_outputs`.

3. **Python** — Prefer the project venv (`uv sync`) or the Docker image so `torch`, `transformers`, and paths match `uv.lock`.

4. **Compose UID** — If you use plain `docker compose` (not `task docker:compose-run`), set `DOCKER_UID` / `DOCKER_GID` so files written to `external_outputs` are owned by your user (`docker-compose.yml` comments).

5. **Read-only `data/`** — Default mount is `data:ro`. Generation that writes under `data/` (e.g. MSC personas) needs `task docker:run-data-rw`.

## 3. Smoke test: prove keys + pipeline (~50 questions)

Use a **truncated copy** of the benchmark (full conversations, fewer `qa` rows) so failures are fast and cheap.

```bash
# Host (from repo root, venv active)
python scripts/slice_locomo_qa.py \
  --input data/locomo10.json \
  --output data/locomo10_smoke_50qa.json \
  --max-questions 50 \
  --overwrite
```

Or run the wrapper (slice + one small eval):

```bash
bash scripts/smoke_eval_qa.sh
# Optional: SMOKE_MAX_QUESTIONS=20 SMOKE_MODEL=gpt-3.5-turbo bash scripts/smoke_eval_qa.sh
```

Docker:

```bash
task docker:run -- bash scripts/smoke_eval_qa.sh
```

Check:

- `outputs/locomo10_smoke_qa.json` (or `external_outputs/...` on the host) contains `*_prediction` fields.
- `outputs/locomo10_smoke_qa_stats.json` exists (written by `evaluate_qa.py`).

**Non-RAG full-context** evaluation does **not** need observation/summary pickle files — only the JSON benchmark + API.

## 4. Full benchmark run (this repo’s evaluators)

**Full-context QA** (model sees truncated conversation in the prompt — no DRAGON index):

```bash
task docker:run -- bash scripts/evaluate_gpts.sh
```

That loops several OpenAI model aliases and writes under `OUT_DIR`. Use a dedicated `QA_OUTPUT_FILE` if you want to avoid overwriting (set in `env.sh` or export before the script).

**Built-in RAG** (for parity with the paper’s retriever setup — separate from your external memory):

1. Generate observations (LLM + embeddings):

   ```bash
   task docker:run -- bash scripts/generate_observations.sh
   ```

2. Generate session summaries + embeddings:

   ```bash
   task docker:run -- bash scripts/generate_session_summaries.sh
   ```

3. Run RAG QA:

   ```bash
   task docker:run -- bash scripts/evaluate_rag_gpts.sh
   ```

### Critical naming rule for RAG pickles

`task_eval/gpt_utils.py` loads embeddings using:

- **Dataset stem** = basename of `--data-file` **without** `.json` (e.g. `locomo10` for `locomo10.json`).
- **Files** = `{stem}_observation_{sample_id}.pkl`, `{stem}_session_summary_{sample_id}.pkl`, `{stem}_dialog_{sample_id}.pkl`.

The generation scripts build pickle names from `--out-file` on `get_facts.py` / `get_session_summaries.py`. Keep this pattern aligned:

- Data: `foo.json`
- Observations JSON: e.g. `outputs/foo_observation.json` → pickles `outputs/foo_observation_{sample_id}.pkl`
- Summaries JSON: e.g. `outputs/foo_session_summary.json` → pickles `outputs/foo_session_summary_{sample_id}.pkl`

Default `env.sh` uses `locomo10_observation.json` / `locomo10_session_summary.json` with `DATA_FILE_PATH=./data/locomo10.json` — that matches.

If you run smoke **RAG** on `data/locomo10_smoke_50qa.json`, set `DATA_FILE_PATH` to that file **and** use output stems **`locomo10_smoke_50qa_observation.json`** (and same for summaries) so the pickle prefix matches the data stem `locomo10_smoke_50qa`.

## 5. Integrating an external memory system (outline)

For a **copy-paste prompt** aimed at a coding agent in the memory-system repo (ingestion API, QA loop, output JSON contract), see [MEMORY_SYSTEM_INTEGRATION_AGENT_PROMPT.md](MEMORY_SYSTEM_INTEGRATION_AGENT_PROMPT.md).

This repository does not implement your memory service. A practical split:

1. **Ingest** — For each `sample_id` in `locomo10.json`, load `conversation` (sessions, turns, timestamps) into your store using the same IDs you will need for scoring (`evidence` in `qa` refers to dialog ids).

2. **Query** — For each benchmark question, your system returns retrieved text (and optionally ids). Map that to whatever LoCoMo expects for analysis (e.g. compare retrieved ids to `evidence` if you track them).

3. **Answer** — Run your LLM with **only** retrieved context + question, or mirror this repo’s prompt shape in `task_eval/gpt_utils.py` for comparability.

4. **Metrics** — `task_eval/evaluation.py` / `evaluation_stats.py` expect prediction fields on each `qa` item; you can reuse them once your runner writes the same JSON shape, or export your results and join on `sample_id` + question index.

Until that adapter exists, use §3 to confirm OpenAI (or another provider you wire similarly) and file paths work; use §4 for a full in-repo baseline.

## 6. Checklist (short)

- [ ] `mkdir -p external_outputs` (Docker) or ensure `OUT_DIR` exists
- [ ] Keys in `.env.docker` or external env file
- [ ] `task docker:build` (or `uv sync` on host)
- [ ] `bash scripts/smoke_eval_qa.sh` → predictions + `*_stats.json`
- [ ] Full run: `bash scripts/evaluate_gpts.sh` (or subset via sliced JSON + single `evaluate_qa.py` invocation)
- [ ] RAG only if needed: observations + summaries generated with **matching** `foo.json` / `foo_observation*` / `foo_session_summary*` stems
