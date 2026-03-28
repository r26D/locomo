# Prompt for a coding agent (memory-system repository)

This file is meant to be **copied into the other repo** (your memory / RAG / agent service) and given to a coding agent or developer. It describes the **LoCoMo benchmark side** of the workflow so you can implement **ingestion**, **question answering**, and **evaluation-ready outputs** without re-deriving formats from the LoCoMo codebase.

---

## Copy from here: agent instructions

You are working in the **memory system** repository. Implement a small, explicit interface so this system can participate in the **LoCoMo** long-term conversational memory benchmark (ACL 2024). The benchmark data and scoring code live in a **separate** project (the LoCoMo repo); your job is only the **memory-system side**: ingest conversations, answer benchmark questions using retrieved memory, and emit results that LoCoMo (or a thin adapter script) can score.

### Background

- LoCoMo evaluation uses a JSON file (typically `locomo10.json`): a **top-level array** of **samples** (10 conversations in the public release, ~2k QA items total).
- Each sample is independent: **clear or isolate memory between `sample_id` values** so sessions from one conversation never leak into another.
- The benchmark does **not** call your service automatically. A runner (in this repo or CI) will either: (1) call your API/CLI per sample and per question, or (2) export JSON for offline scoring.

### Input: benchmark sample shape (what to ingest)

For each element of the LoCoMo JSON array:

| Field | Purpose for you |
|--------|------------------|
| `sample_id` | Stable string id; use as namespace / tenant / index name for this conversation. |
| `conversation` | Multi-session dialogue. Keys include `speaker_a`, `speaker_b`, `session_<n>`, `session_<n>_date_time` for chronological session index `<n>` (1-based in practice). |
| Session turns | Each `session_<n>` is an array of turns. Each turn should include at least: `speaker`, `dia_id` (dialogue id string, used in gold `evidence`), `text`. Optional: `img_url`, `blip_caption`, image search metadata — **images are not shipped**; URLs/captions may still be useful as text. |

**Ingestion contract (implement clearly):**

1. **Order**: Ingest sessions in ascending session number; within each session, ingest turns in **array order** (conversation order).
2. **Content**: Store enough text per turn for retrieval (raw `text`; optionally prepend session date from `session_<n>_date_time` if your system does not store metadata separately).
3. **Ids**: Preserve `dia_id` on each stored chunk or in metadata so you can optionally return **retrieved ids** for recall-style metrics (see below).
4. **Isolation**: After finishing all QA for one `sample_id`, **reset** memory for the next sample (new collection, truncate, or explicit delete).

### Input: questions (what to answer)

Within the same sample object, field **`qa`** is an array of question objects. For each item you need at least:

| Field | Meaning |
|--------|---------|
| `question` | The text to send to your QA pipeline (after retrieval from memory loaded for this `sample_id` only). |
| `category` | Integer 1–5 (see below). May affect prompt shaping if you want to match LoCoMo reference evaluators. |
| `answer` | Gold reference (may be absent on some rows; see `adversarial_answer`). **Do not** feed gold answers to the model during inference. |
| `adversarial_answer` | Used for category **5** when present; evaluation treats these as distractors. |
| `evidence` | List of dialog id references (when present) pointing to supporting turns; used for **retrieval recall** metrics if you export retrieved ids. |

**Category labels (LoCoMo QA):**

1. Multi-hop  
2. Temporal (LoCoMo’s reference prompts sometimes append instructions to use conversation dates; consider appending similar guidance for fair comparison.)  
3. Open-domain / commonsense (gold may use `;`-separated acceptable answers; scoring uses the first segment.)  
4. Single-hop  
5. Adversarial (model should often indicate **no answer** / not mentioned when the fact is not in the dialog; scoring checks for phrases like “no information” / “not mentioned” vs hallucination.)

### Output: predictions (what to produce)

Produce a JSON file (or stream) that mirrors the benchmark structure enough to score:

- Top-level: **array of objects**, one per `sample_id` you evaluated (same order as input is nice but not required if `sample_id` is present).
- Each object must include:
  - `sample_id` (string, same as input).
  - `qa`: array **parallel to the input `qa` array** for that sample (same length, same order). Each element should be the **input QA object extended** with:
    - **`<run_id>_prediction`** (string): your model’s short answer for that question.  
      Example key: `memory_eval_prediction` or `my_system_v1_prediction`. LoCoMo’s `eval_question_answering` in `task_eval/evaluation.py` uses a configurable `eval_key` suffix `_prediction` pattern when driven from `evaluate_qa.py` (which uses model-specific keys). For hand-off scoring, use **one consistent key** and document it; a one-line adapter can rename the key to match `evaluate_qa.py` if needed.
    - **Optional** **`<run_id>_context`** (list): ids of retrieved turns / chunks (strings). If present and `evidence` is non-empty, LoCoMo computes recall against `evidence` (dialog ids like `D1:3` or similar formats in the dataset). Session-summary RAG in LoCoMo uses ids starting with `S`; dialog mode uses `dia_id` values. Prefer returning **`dia_id`** strings aligned with the conversation if you want dialog-style recall.

Do **not** strip original fields (`question`, `answer`, `category`, `evidence`, etc.); scoring needs gold fields.

### Interface shape (what to implement in this repo)

Deliver **at least one** of:

1. **CLI**  
   - `ingest --sample-id <id> --locomo-json <path>` (or ingest from stdin)  
   - `answer --sample-id <id> --questions-json <path>` or `answer` reading questions from the same file  
   - `run-eval --input locomo10.json --output predictions.json` that loops samples, clears between samples, fills predictions  

2. **Library API**  
   - `load_sample(conversation: dict, sample_id: str) -> None`  
   - `answer_question(sample_id: str, question: str, category: int) -> str`  
   - Optional: `answer_question_with_provenance(...) -> (str, list[str])` for `_context` ids  

3. **HTTP API** (if that fits your architecture)  
   - `POST /sessions/{sample_id}/ingest` with conversation body  
   - `POST /sessions/{sample_id}/qa` with `{ "question", "category" }` returning `{ "answer", "retrieved_ids": [] }`  
   - `DELETE /sessions/{sample_id}` between benchmark samples  

Requirements:

- **Deterministic sample boundaries**: no cross-sample retrieval.  
- **Configurable model and prompts** via env or config file (for reproducibility).  
- **Logging**: sample_id, question index, latency, errors; continue or fail fast — document the policy.  
- **Smoke mode**: support limiting to first *N* questions or first *M* samples (for cheap CI).  

### Testing expectations

- Unit tests: ingestion preserves order and ids; empty memory returns safe behavior; category-5 questions do not invent facts when memory is empty.  
- Integration test: run on a **tiny** slice of LoCoMo JSON (e.g. one sample, five questions) and assert output JSON validates (lengths, required keys).  

### Scoring (done in LoCoMo repo, not here)

After `predictions.json` exists, the LoCoMo project can merge predictions with gold `qa` and call `eval_question_answering` / `analyze_aggr_acc` from `task_eval/evaluation.py` and `task_eval/evaluation_stats.py`, or run a small script that loads your output and prints aggregate F1. You do **not** need to copy LoCoMo’s metric code into the memory repo unless you want duplicate reporting.

### References (human: point your agent at these paths in the LoCoMo clone)

- Dataset description: `README.MD` (Data section).  
- QA scoring: `task_eval/evaluation.py` (`eval_question_answering`).  
- Reference prompt behavior (OpenAI path): `task_eval/gpt_utils.py` (temporal / adversarial formatting).  
- Prep / Docker / smoke workflow: `docs/BENCHMARK_PREP.md`.  

### Constraints

- Do not bake in hard-coded paths to the LoCoMo repo; accept paths via CLI or config.  
- Treat the benchmark file as **read-only**; write outputs to a separate file.  
- Respect API rate limits and support resumable runs (skip questions that already have a prediction key in the output file, if implementing incremental writes).

---

## End of copy-paste block

### For maintainers in the LoCoMo repo

- Update this prompt if the on-disk JSON schema or metric expectations change.  
- When the memory team produces `predictions.json`, a minimal merge step is: for each `sample_id`, copy `<run_id>_prediction` into the key name your scoring script expects, or pass `eval_key` if you add a small standalone scorer wrapper.
