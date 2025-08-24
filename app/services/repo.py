"""Data repository interfaces and implementations.

This module defines an abstract :class:`Repository` interface for storing
and querying documents with vector embeddings.  Concrete implementations are
provided for SQLite (intended for local development), PostgreSQL with the
`pgvector` extension and Azure Cosmos DB's Mongo API.  The actual backend used
at runtime can be selected via the ``REPO_BACKEND`` environment variable which
may be one of ``"sqlite"``, ``"postgres"`` or ``"cosmos"``.  Each backend
expects a corresponding connection string in ``REPO_CONNECTION_STRING``.

The implementations are intentionally lightweight and aim to provide a common
shape for experimentation and unit tests.  They are not optimised for
performance and only cover the minimal functionality required by the demo
application.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional

# Type alias for readability
Embedding = List[float]


class Repository(ABC):
    """Abstract repository for storing documents and embeddings."""

    @abstractmethod
    def add_document(self, text: str, embedding: Embedding, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Persist a document with its vector embedding."""

    @abstractmethod
    def similarity_search(self, embedding: Embedding, k: int = 5) -> List[Dict[str, Any]]:
        """Return the ``k`` most similar documents for the supplied embedding."""

    @abstractmethod
    def close(self) -> None:
        """Release any underlying resources."""


class SQLiteRepository(Repository):
    """Simple SQLite based repository used for local development."""

    def __init__(self, conn_str: str | None = None) -> None:
        import sqlite3

        self.path = conn_str or "./local.db"
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), "sql", "sqlite_schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def add_document(self, text: str, embedding: Embedding, metadata: Optional[Dict[str, Any]] = None) -> None:
        metadata_json = json.dumps(metadata or {})
        embedding_json = json.dumps(embedding)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO documents(text, embedding, metadata) VALUES (?, ?, ?)",
            (text, embedding_json, metadata_json),
        )
        self.conn.commit()

    def similarity_search(self, embedding: Embedding, k: int = 5) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT id, text, embedding, metadata FROM documents").fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            stored = json.loads(row["embedding"])
            score = _dot_product(stored, embedding)
            results.append({"id": row["id"], "text": row["text"], "metadata": json.loads(row["metadata"]), "score": score})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]

    def close(self) -> None:
        self.conn.close()


class PostgresPgvectorRepository(Repository):
    """PostgreSQL repository leveraging the pgvector extension."""

    def __init__(self, conn_str: str) -> None:
        import psycopg

        self.conn = psycopg.connect(conn_str)
        self._init_db()

    def _init_db(self) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), "sql", "postgres_schema.sql")
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            with open(schema_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())
            self.conn.commit()

    def add_document(self, text: str, embedding: Embedding, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents(text, embedding, metadata) VALUES (%s, %s, %s)",
                (text, embedding, json.dumps(metadata or {})),
            )
            self.conn.commit()

    def similarity_search(self, embedding: Embedding, k: int = 5) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, text, metadata, 1 - (embedding <-> %s) AS score FROM documents ORDER BY embedding <-> %s LIMIT %s",
                (embedding, embedding, k),
            )
            rows = cur.fetchall()
        return [
            {"id": row[0], "text": row[1], "metadata": row[2], "score": float(row[3])}
            for row in rows
        ]

    def close(self) -> None:
        self.conn.close()


class CosmosMongoRepository(Repository):
    """Azure Cosmos DB repository using the Mongo API."""

    def __init__(self, conn_str: str, db_name: str = "demo", collection: str = "documents") -> None:
        from pymongo import MongoClient

        self.client = MongoClient(conn_str)
        self.collection = self.client[db_name][collection]
        # Ensure an index for vector search when supported.  The specification
        # for the operator is subject to change; creating a regular index keeps
        # inserts functional for the demo environment.
        try:
            self.collection.create_index("embedding")
        except Exception:
            pass

    def add_document(self, text: str, embedding: Embedding, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.collection.insert_one({"text": text, "embedding": embedding, "metadata": metadata or {}})

    def similarity_search(self, embedding: Embedding, k: int = 5) -> List[Dict[str, Any]]:
        # The Mongo API for vector search uses the $vectorSearch pipeline.  To
        # keep the implementation lightweight and dependency free we fall back
        # to a client-side similarity computation if the pipeline is not
        # available.
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "queryVector": embedding,
                        "path": "embedding",
                        "numCandidates": 200,
                        "limit": k,
                    }
                }
            ]
            rows = list(self.collection.aggregate(pipeline))
            return [
                {"id": str(row.get("_id")), "text": row.get("text"), "metadata": row.get("metadata", {}), "score": row.get("score", 0.0)}
                for row in rows
            ]
        except Exception:
            rows = list(self.collection.find())
            results: List[Dict[str, Any]] = []
            for row in rows:
                score = _dot_product(row.get("embedding", []), embedding)
                results.append({"id": str(row.get("_id")), "text": row.get("text"), "metadata": row.get("metadata", {}), "score": score})
            results.sort(key=lambda r: r["score"], reverse=True)
            return results[:k]

    def close(self) -> None:
        self.client.close()


def _dot_product(a: Iterable[float], b: Iterable[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def create_repository_from_env() -> Repository:
    """Create a repository instance based on environment configuration."""

    backend = os.environ.get("REPO_BACKEND", "sqlite").lower()
    conn_str = os.environ.get("REPO_CONNECTION_STRING")

    if backend == "postgres":
        if not conn_str:
            raise ValueError("REPO_CONNECTION_STRING must be set for Postgres backend")
        return PostgresPgvectorRepository(conn_str)
    if backend == "cosmos":
        if not conn_str:
            raise ValueError("REPO_CONNECTION_STRING must be set for Cosmos backend")
        db_name = os.environ.get("REPO_DB_NAME", "demo")
        collection = os.environ.get("REPO_COLLECTION", "documents")
        return CosmosMongoRepository(conn_str, db_name=db_name, collection=collection)
    # Default to SQLite
    return SQLiteRepository(conn_str)
