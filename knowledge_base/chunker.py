"""
Markdown document chunking for knowledge base indexing.
Splits documents by headers while preserving context.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    content: str
    metadata: dict
    chunk_index: int
    source_file: str
    section_header: str


class MarkdownChunker:
    """
    Intelligent markdown chunking that preserves section context.
    Splits by headers first, then by size if needed.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_document(self, content: str, source_file: str) -> List[DocumentChunk]:
        """
        Chunk a markdown document into smaller pieces.

        Strategy:
        1. Split by markdown headers (##, ###) to preserve section context
        2. If section is too large, split by paragraphs
        3. If paragraph is too large, split by sentences with overlap
        4. Maintain section header in metadata for retrieval context
        """
        chunks = []
        sections = self._split_by_headers(content)

        for section_header, section_content in sections:
            if not section_content.strip():
                continue

            # Infer document type from path
            doc_type = self._infer_type(source_file)

            if len(section_content) <= self.chunk_size:
                # Section fits in one chunk
                chunk_content = section_content
                if section_header:
                    chunk_content = f"## {section_header}\n\n{section_content}"

                chunks.append(DocumentChunk(
                    content=chunk_content,
                    metadata={
                        "source": source_file,
                        "section": section_header or "Introduction",
                        "type": doc_type
                    },
                    chunk_index=len(chunks),
                    source_file=source_file,
                    section_header=section_header or "Introduction"
                ))
            else:
                # Need to split large sections
                sub_chunks = self._split_with_overlap(section_content)
                for i, sub_chunk in enumerate(sub_chunks):
                    header_text = section_header or "Introduction"
                    if len(sub_chunks) > 1:
                        chunk_content = f"## {header_text} (Part {i + 1})\n\n{sub_chunk}"
                    else:
                        chunk_content = f"## {header_text}\n\n{sub_chunk}"

                    chunks.append(DocumentChunk(
                        content=chunk_content,
                        metadata={
                            "source": source_file,
                            "section": header_text,
                            "part": i + 1 if len(sub_chunks) > 1 else None,
                            "type": doc_type
                        },
                        chunk_index=len(chunks),
                        source_file=source_file,
                        section_header=header_text
                    ))

        return chunks

    def _split_by_headers(self, content: str) -> List[Tuple[str, str]]:
        """Split content by markdown headers (## and ###)."""
        # Pattern to match ## or ### headers
        header_pattern = r'^(#{2,3})\s+(.+?)$'

        lines = content.split('\n')
        sections = []
        current_header = ""
        current_content = []

        for line in lines:
            match = re.match(header_pattern, line)
            if match:
                # Save previous section
                if current_content or current_header:
                    sections.append((
                        current_header,
                        '\n'.join(current_content).strip()
                    ))

                # Start new section
                current_header = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content or current_header:
            sections.append((
                current_header,
                '\n'.join(current_content).strip()
            ))

        return sections

    def _split_with_overlap(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        # First try splitting by paragraphs
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            if current_length + para_length <= self.chunk_size:
                current_chunk.append(para)
                current_length += para_length + 2  # +2 for \n\n
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))

                # Handle oversized paragraphs
                if para_length > self.chunk_size:
                    # Split by sentences
                    sentences = self._split_sentences(para)
                    sent_chunks = self._group_sentences(sentences)
                    chunks.extend(sent_chunks)
                    current_chunk = []
                    current_length = 0
                else:
                    current_chunk = [para]
                    current_length = para_length

        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def _group_sentences(self, sentences: List[str]) -> List[str]:
        """Group sentences into chunks with overlap."""
        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sent_length = len(sentence)

            if current_length + sent_length <= self.chunk_size:
                current_chunk.append(sentence)
                current_length += sent_length + 1
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))

                    # Keep overlap
                    overlap_size = 0
                    overlap_sentences = []
                    for s in reversed(current_chunk):
                        if overlap_size + len(s) <= self.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_size += len(s) + 1
                        else:
                            break

                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s) for s in current_chunk) + len(current_chunk)
                else:
                    current_chunk = [sentence]
                    current_length = sent_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _infer_type(self, source_file: str) -> str:
        """Infer document type from file path."""
        source_lower = source_file.lower()

        if 'infrastructure' in source_lower:
            return 'infrastructure'
        elif 'application' in source_lower:
            return 'application'
        elif 'monitoring' in source_lower:
            return 'monitoring'
        else:
            return 'general'
