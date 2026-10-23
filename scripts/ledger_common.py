#!/usr/bin/env python3
"""Shared helpers for the /ledger/ layer.

`anchor()` returns the timestamp of the newest stored capture. Every generator stamps its
output with it instead of the wall clock, so that rebuilding the layer in CI reproduces
the committed bytes exactly (the workflow enforces that with `git diff --exit-code`).
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ledger"


def anchor() -> str:
    try:
        m = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "1970-01-01T00:00:00Z"
    stamps = [c.get("fetched_at") or "" for c in m.get("captures", [])]
    return max((s for s in stamps if s), default="1970-01-01T00:00:00Z")
