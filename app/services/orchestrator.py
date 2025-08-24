"""Simple orchestrator service maintaining per-session state.

This module defines a minimal workflow that can be used by other parts of the
application.  It demonstrates how to persist state for each session and run a
series of nodes that operate on that state.

The orchestrator exposes four nodes:

* :class:`AskQuestion` – stores the current question in session state.
* :class:`CollectAnswer` – records an answer for the current question.
* :class:`ValidateAnswer` – checks the answer using a supplied validator.
* :class:`RouteNext` – decides what the next step should be based on the
  validation result.

The :func:`run_graph` function is the public entry point for executing the
workflow for a particular session.  The per-session state is kept in the
``_repository`` object defined below.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class SessionStateRepository:
    """In-memory repository for persisting session state."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str) -> dict[str, Any]:
        """Return the state for *session_id*, creating it if necessary."""
        return self._store.setdefault(session_id, {"history": []})

    def save(self, session_id: str, state: dict[str, Any]) -> None:
        """Persist *state* for *session_id*."""
        self._store[session_id] = state


_repository = SessionStateRepository()


@dataclass
class AskQuestion:
    """Node that records the current question."""

    def __call__(self, state: dict[str, Any], question: str) -> str:
        state["current_question"] = question
        return question


@dataclass
class CollectAnswer:
    """Node that stores the answer for the current question."""

    def __call__(self, state: dict[str, Any], answer: str) -> str:
        question = state.get("current_question")
        state["current_answer"] = answer
        state.setdefault("history", []).append((question, answer))
        return answer


@dataclass
class ValidateAnswer:
    """Node that validates the collected answer."""

    validator: Callable[[str], bool] | None = None

    def __call__(self, state: dict[str, Any]) -> bool:
        answer = state.get("current_answer", "")
        is_valid = True if self.validator is None else self.validator(answer)
        state["is_valid"] = is_valid
        return is_valid


@dataclass
class RouteNext:
    """Node that determines the next action based on validation."""

    def __call__(self, state: dict[str, Any]) -> str:
        next_step = "complete" if state.get("is_valid") else "retry"
        state["next_step"] = next_step
        return next_step


def run_graph(
    session_id: str,
    question: str,
    answer: str,
    validator: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Execute the node graph for ``session_id``.

    The workflow is:

    1. :class:`AskQuestion` – store the question.
    2. :class:`CollectAnswer` – record the answer.
    3. :class:`ValidateAnswer` – validate the answer.
    4. :class:`RouteNext` – determine the next step.

    The updated session state is returned.
    """

    state = _repository.get(session_id)
    AskQuestion()(state, question)
    CollectAnswer()(state, answer)
    ValidateAnswer(validator)(state)
    RouteNext()(state)
    _repository.save(session_id, state)
    return state
