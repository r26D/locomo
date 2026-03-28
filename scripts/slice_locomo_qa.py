#!/usr/bin/env python3
"""
Build a smaller LoCoMo JSON for smoke tests by keeping full conversations but
truncating each sample's `qa` list. Use this before wiring an external memory
system so you can validate APIs, keys, and I/O with tens of questions instead
of ~2k.

Example:
  python scripts/slice_locomo_qa.py \\
    --input data/locomo10.json \\
    --output data/locomo10_smoke_50qa.json \\
    --max-questions 50

For RAG-style flows in this repo, regenerate observation/summary artifacts
against the same --output filename stem (see docs/BENCHMARK_PREP.md).
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path, help="Source LoCoMo JSON (e.g. data/locomo10.json)")
    p.add_argument("--output", required=True, type=Path, help="Written JSON (parent dir must exist)")
    p.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Include only the first N conversations (file order). Default: all samples.",
    )
    p.add_argument(
        "--max-questions",
        type=int,
        required=True,
        help="Total QA items to keep, filled in sample order (first sample first, then next, ...).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace output if it exists.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_questions < 1:
        raise SystemExit("--max-questions must be >= 1")

    data: list[dict[str, Any]] = json.loads(args.input.read_text())
    if not isinstance(data, list):
        raise SystemExit("Expected top-level JSON array of samples")

    if args.max_samples is not None:
        if args.max_samples < 1:
            raise SystemExit("--max-samples must be >= 1 when set")
        data = data[: args.max_samples]

    remaining = args.max_questions
    out: list[dict[str, Any]] = []

    for sample in data:
        if remaining <= 0:
            break
        row = json.loads(json.dumps(sample))
        qa = row.get("qa") or []
        if not isinstance(qa, list):
            raise SystemExit("sample %r: qa must be a list" % row.get("sample_id"))
        take = min(remaining, len(qa))
        row["qa"] = qa[:take]
        remaining -= take
        out.append(row)

    if not out or all(len(s.get("qa") or []) == 0 for s in out):
        raise SystemExit("No QA written; check --max-samples / --max-questions")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and not args.overwrite:
        raise SystemExit("Output exists: %s (use --overwrite)" % args.output)

    text = json.dumps(out, indent=2)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(text)
    shutil.move(str(tmp), args.output)

    total_qa = sum(len(s.get("qa") or []) for s in out)
    print("Wrote %s (%s samples, %s QA)" % (args.output, len(out), total_qa))


if __name__ == "__main__":
    main()
