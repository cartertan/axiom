from datetime import datetime, timezone

import chromadb

from src.core.ollama_client import OllamaClient


class AxiomMemory:
    def __init__(self, db_path: str = "memory/chroma_db"):
        self._client = chromadb.PersistentClient(path=db_path)
        self._ollama = OllamaClient()
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name="axiom_memory",
            metadata={"hnsw:space": "cosine"},
        )

    def store_interaction(
        self,
        task_type: str,
        summary: str,
        entities: list = None,
        model_used: str = "",
        metadata: dict = None,
    ) -> None:
        """Embed summary and store in ChromaDB with task metadata."""
        if entities is None:
            entities = []
        if metadata is None:
            metadata = {}

        embedding = self._ollama.embed(summary)
        timestamp = datetime.now(timezone.utc).isoformat()
        doc_id = f"{task_type}_{timestamp}"

        combined_metadata = {
            "task_type": task_type,
            "model_used": model_used,
            "timestamp": timestamp,
            "entities": ", ".join(entities),
            **metadata,
        }

        self._collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[summary],
            metadatas=[combined_metadata],
        )

    def retrieve_context(self, query: str, n_results: int = 3) -> str:
        """Return formatted string of relevant past interactions for prompt injection."""
        count = self._collection.count()
        if count == 0:
            return ""

        embedding = self._ollama.embed(query)
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(n_results, count),
            include=["documents", "metadatas"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            return ""

        lines = ["[Relevant past context:]"]
        for doc, meta in zip(docs, metas):
            ts = meta.get("timestamp", "")[:10]
            task = meta.get("task_type", "")
            lines.append(f"- [{ts}] ({task}) {doc}")

        return "\n".join(lines)

    def get_recent_interactions(self, n: int = 20) -> list:
        """Return the n most recent interactions, newest first."""
        count = self._collection.count()
        if count == 0:
            return []

        results = self._collection.get(include=["documents", "metadatas"])
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])

        interactions = [
            {
                "summary": doc,
                "task_type": meta.get("task_type", ""),
                "model_used": meta.get("model_used", ""),
                "timestamp": meta.get("timestamp", ""),
            }
            for doc, meta in zip(docs, metas)
        ]
        interactions.sort(key=lambda i: i["timestamp"], reverse=True)
        return interactions[:n]

    def clear_memory(self) -> None:
        """Delete and recreate the memory collection."""
        self._client.delete_collection("axiom_memory")
        self._collection = self._get_or_create_collection()
