"""
Vector store operations using ChromaDB for semantic search.
"""

from typing import List, Optional
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings as ChromaSettings


@dataclass
class SearchResult:
    """Represents a search result from the vector store."""
    content: str
    source_file: str
    section: str
    score: float
    metadata: dict


class VectorStore:
    """ChromaDB-based vector store for runbook search."""

    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "runbooks"
    ):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedding_function = None

    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict]
    ):
        """
        Add documents to the vector store.

        Args:
            ids: Unique identifiers for documents
            documents: Document texts
            embeddings: Pre-computed embeddings
            metadatas: Metadata for each document
        """
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_type: Optional[str] = None,
        min_score: float = 0.5
    ) -> List[SearchResult]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            filter_type: Optional filter by document type
            min_score: Minimum similarity score threshold

        Returns:
            List of SearchResult objects
        """
        where_filter = {"type": filter_type} if filter_type else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []

        if not results["documents"] or not results["documents"][0]:
            return search_results

        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # Convert cosine distance to similarity score
            score = 1 - distance

            if score >= min_score:
                search_results.append(SearchResult(
                    content=doc,
                    source_file=metadata.get("source", "unknown"),
                    section=metadata.get("section", ""),
                    score=score,
                    metadata=metadata
                ))

        return search_results

    def delete_collection(self):
        """Delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self._collection = None
        except Exception:
            pass  # Collection might not exist

    def get_count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def clear(self):
        """Clear all documents from the collection."""
        self.delete_collection()
        self._collection = None
