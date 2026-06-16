import re
from pathlib import Path

import chromadb

from src.core.ollama_client import OllamaClient

_COLLECTION_NAME = "axiom_pki_knowledge"
_TARGET_CHUNK_WORDS = 300
_MIN_CHUNK_WORDS = 20


class PKIIndexer:
    def __init__(self, db_path: str = "memory/chroma_db"):
        self._client = chromadb.PersistentClient(path=db_path)
        self._ollama = OllamaClient()
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _chunk_text(self, text: str) -> list:
        """Split text into ~300-word chunks, preserving paragraph boundaries."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_paragraphs = []
        current_words = 0

        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            if current_paragraphs and current_words + paragraph_words > _TARGET_CHUNK_WORDS:
                chunks.append("\n\n".join(current_paragraphs))
                current_paragraphs = []
                current_words = 0
            current_paragraphs.append(paragraph)
            current_words += paragraph_words

        if current_paragraphs:
            chunks.append("\n\n".join(current_paragraphs))

        return chunks

    def _clean_chunk(self, chunk: str) -> str:
        """Strip non-ASCII characters and normalise whitespace."""
        ascii_text = chunk.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_text).strip()

    def index_knowledge_base(self, path: str = "knowledge/pki/") -> None:
        """Read all .md files under path, chunk, clean, embed, and store in ChromaDB."""
        md_files = sorted(Path(path).glob("*.md"))

        ids, embeddings, documents, metadatas = [], [], [], []
        files_indexed = 0

        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            raw_chunks = self._chunk_text(text)
            chunk_index = 0

            for raw_chunk in raw_chunks:
                cleaned = self._clean_chunk(raw_chunk)
                if len(cleaned.split()) < _MIN_CHUNK_WORDS:
                    continue

                embedding = self._ollama.embed(cleaned)
                ids.append(f"{md_file.stem}_{chunk_index}")
                embeddings.append(embedding)
                documents.append(cleaned)
                metadatas.append(
                    {"source_file": md_file.name, "chunk_index": chunk_index}
                )
                chunk_index += 1

            if chunk_index > 0:
                files_indexed += 1

        if ids:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

        print(f"{len(ids)} chunks indexed from {files_indexed} files")

    def rebuild(self, path: str = "knowledge/pki/") -> None:
        """Delete the existing collection and reindex from scratch."""
        self._client.delete_collection(_COLLECTION_NAME)
        self._collection = self._get_or_create_collection()
        self.index_knowledge_base(path)
