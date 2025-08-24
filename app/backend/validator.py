"""Simple response validator to compute a score for responses.

This module provides a basic ``evaluate_response`` function which
assigns a score between 0.0 and 1.0 based on heuristics about the
returned answer.  The scorer is intentionally lightweight so it can
serve as an example for how responses might be evaluated.
"""
from __future__ import annotations

from typing import Any


def evaluate_response(response: dict[str, Any]) -> float:
    """Evaluate a response and return a score between 0.0 and 1.0.

    Scoring rules:
    * If the response is missing an ``answer`` field or the answer is
      empty, return ``0.0``.
    * If the answer contains "i don't know" (case insensitive), return
      ``0.0``.
    * If the answer has fewer than 20 words, return ``0.5``.
    * Otherwise, return ``1.0``.

    The heuristics are intentionally simple to keep the module
    lightweight; they can be extended with additional logic as needed.
    """

    answer = str(response.get("answer", "")).strip()
    if not answer:
        return 0.0

    lowered = answer.lower()
    if "i don't know" in lowered or "i do not know" in lowered:
        return 0.0

    word_count = len(answer.split())
    if word_count < 20:
        return 0.5

    return 1.0
