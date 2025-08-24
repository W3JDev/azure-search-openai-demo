import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "app" / "backend"))
from validator import evaluate_response


def test_missing_answer():
    assert evaluate_response({}) == 0.0


def test_unknown_answer():
    assert evaluate_response({"answer": "I don't know"}) == 0.0


def test_short_answer():
    assert evaluate_response({"answer": "Yes"}) == 0.5


def test_long_answer():
    long_text = "word " * 20
    assert evaluate_response({"answer": long_text.strip()}) == 1.0
