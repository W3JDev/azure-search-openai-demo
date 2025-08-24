"""Simple graph-based orchestrator for routing requests.

The orchestrator holds a very small directed graph where the
entry point decides which branch to follow based on predicates.
This module is intentionally lightweight so it can be used during
unit testing without external dependencies.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable

Predicate = Callable[[dict[str, Any]], bool]


@dataclass
class GraphNode:
    """A node in the routing graph."""

    name: str
    edges: Iterable[tuple[Predicate, GraphNode]] = field(default_factory=list)

    def connect(self, condition: Predicate, node: GraphNode) -> None:
        self.edges = tuple(list(self.edges) + [(condition, node)])


class Orchestrator:
    """Routes requests through a simple directed graph."""

    def __init__(self, start: GraphNode):
        self.start = start

    def route(self, payload: dict[str, Any], default: str) -> str:
        """Return the name of the next node based on predicates.

        Parameters
        ----------
        payload: Dict[str, Any]
            Request payload used to evaluate routing predicates.
        default: str
            Default node name returned when no predicate matches.
        """
        for condition, node in self.start.edges:
            try:
                if condition(payload):
                    return node.name
            except Exception:
                # If a condition raises we ignore it and fall back to default.
                continue
        return default


def build_default_orchestrator() -> Orchestrator:
    """Create an orchestrator with chat/data routing logic.

    The decision is based on ``payload["context"]["task"]``.  When the
    value is ``"chat"`` the chat route is selected, when ``"data"`` the
    data route is selected.  If the key is missing the caller provided
    ``default`` value from :func:`Orchestrator.route` is used.
    """
    start = GraphNode("start")
    chat = GraphNode("chat")
    data = GraphNode("data")
    start.connect(lambda m: m.get("context", {}).get("task") == "chat", chat)
    start.connect(lambda m: m.get("context", {}).get("task") == "data", data)
    return Orchestrator(start)
