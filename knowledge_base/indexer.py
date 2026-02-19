"""
Knowledge base indexer for runbook files.
Handles embedding generation and vector store population.
"""

import hashlib
from pathlib import Path
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from knowledge_base.chunker import MarkdownChunker, DocumentChunk
from knowledge_base.vector_store import VectorStore
from config.settings import get_settings


class KnowledgeBaseIndexer:
    """
    Indexes markdown runbook files into the vector store.
    """

    def __init__(
        self,
        runbooks_path: Optional[str] = None,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None,
        collection_name: str = "runbooks"
    ):
        """
        Initialize the indexer.

        Args:
            runbooks_path: Path to runbook files
            persist_directory: ChromaDB persistence directory
            embedding_model: Name of the sentence-transformers model
            collection_name: Name of the ChromaDB collection
        """
        settings = get_settings()

        self.runbooks_path = Path(runbooks_path or settings.runbooks_path)
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embedding_model_name = embedding_model or settings.embedding_model

        # Initialize components
        self._embedding_model = None
        self.vector_store = VectorStore(
            persist_directory=self.persist_directory,
            collection_name=collection_name
        )
        self.chunker = MarkdownChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy initialization of embedding model."""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def index_all_runbooks(self, force_reindex: bool = False) -> int:
        """
        Index all markdown files in the runbooks directory.

        Args:
            force_reindex: If True, clears existing index first

        Returns:
            Number of chunks indexed
        """
        if force_reindex:
            self.vector_store.clear()

        all_chunks: List[DocumentChunk] = []

        # Find all markdown files
        md_files = list(self.runbooks_path.rglob("*.md"))

        if not md_files:
            print(f"No markdown files found in {self.runbooks_path}")
            return 0

        print(f"Found {len(md_files)} markdown files")

        # Process each file
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8")
                relative_path = str(md_file.relative_to(self.runbooks_path))

                file_chunks = self.chunker.chunk_document(
                    content=content,
                    source_file=relative_path
                )

                all_chunks.extend(file_chunks)
                print(f"  - {relative_path}: {len(file_chunks)} chunks")

            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                continue

        if not all_chunks:
            print("No chunks to index")
            return 0

        # Generate embeddings in batch
        print(f"\nGenerating embeddings for {len(all_chunks)} chunks...")
        texts = [chunk.content for chunk in all_chunks]
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Generate IDs and prepare metadata
        ids = [self._generate_id(chunk) for chunk in all_chunks]
        metadatas = [chunk.metadata for chunk in all_chunks]

        # Add to vector store
        print("Adding to vector store...")
        self.vector_store.add_documents(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"Successfully indexed {len(all_chunks)} chunks")
        return len(all_chunks)

    def index_single_file(self, file_path: str) -> int:
        """
        Index a single markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Number of chunks indexed
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # Determine relative path
        try:
            relative_path = str(file_path.relative_to(self.runbooks_path))
        except ValueError:
            relative_path = file_path.name

        chunks = self.chunker.chunk_document(
            content=content,
            source_file=relative_path
        )

        if not chunks:
            return 0

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True
        )

        # Add to vector store
        ids = [self._generate_id(chunk) for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        self.vector_store.add_documents(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        return len(chunks)

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_type: Optional[str] = None,
        min_score: float = 0.5
    ):
        """
        Search the knowledge base.

        Args:
            query: Search query
            n_results: Number of results
            filter_type: Optional type filter
            min_score: Minimum similarity score

        Returns:
            List of SearchResult objects
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        )[0]

        return self.vector_store.search(
            query_embedding=query_embedding.tolist(),
            n_results=n_results,
            filter_type=filter_type,
            min_score=min_score
        )

    def _generate_id(self, chunk: DocumentChunk) -> str:
        """Generate a deterministic ID for a chunk."""
        content_hash = hashlib.md5(chunk.content.encode()).hexdigest()[:8]
        return f"{chunk.source_file}_{chunk.chunk_index}_{content_hash}"

    def get_stats(self) -> dict:
        """Get indexer statistics."""
        return {
            "total_chunks": self.vector_store.get_count(),
            "runbooks_path": str(self.runbooks_path),
            "embedding_model": self.embedding_model_name
        }
