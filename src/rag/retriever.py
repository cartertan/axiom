import chromadb

from src.core.ollama_client import OllamaClient

_COLLECTION_NAME = "axiom_pki_knowledge"


class PKIRetriever:
    def __init__(self, db_path: str = "memory/chroma_db"):
        self._client = chromadb.PersistentClient(path=db_path)
        self._ollama = OllamaClient()
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def retrieve(self, query: str, n_results: int = 4) -> str:
        """Embed the query, retrieve the closest PKI knowledge chunks, and
        return a formatted context string with source attribution for
        injection into an agent's prompt."""
        count = self._collection.count()
        if count == 0:
            return "[No PKI knowledge base indexed yet — run the PKIIndexer first.]"

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

        lines = ["[Relevant PKI knowledge base context:]"]
        for doc, meta in zip(docs, metas):
            source = meta.get("source_file", "unknown")
            lines.append(f"- (source: {source}) {doc}")

        return "\n".join(lines)
