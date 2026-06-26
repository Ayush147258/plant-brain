"""Utilities for splitting extracted text into retrieval-friendly chunks."""

import re
from uuid import uuid4


class TextChunker:
    """Pure text chunking helpers for embedding and retrieval workflows."""

    SECTION_HEADER_PATTERN = re.compile(r"^(#{1,3}|\d+\.\d*|[A-Z][A-Z\s]{3,}:)\s", re.MULTILINE)
    SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?।॥\n])\s+")

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 800,
        overlap: int = 100,
        metadata: dict | None = None,
    ) -> list[dict]:
        """Split text into sentence-aware chunks with overlapping context."""

        document_metadata = dict(metadata or {})
        normalized_text = text.strip()
        if not normalized_text:
            return []

        sentences = TextChunker._split_sentences(normalized_text)
        chunks: list[dict] = []
        current_sentences: list[str] = []
        current_length = 0
        search_offset = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            separator_length = 1 if current_sentences else 0
            projected_length = current_length + separator_length + sentence_length

            if current_sentences and projected_length > chunk_size:
                chunk_text_value = " ".join(current_sentences).strip()
                TextChunker._append_chunk(chunks, normalized_text, chunk_text_value, search_offset, document_metadata)
                search_offset = TextChunker._next_search_offset(normalized_text, chunk_text_value, search_offset)

                overlap_text = TextChunker._get_overlap_text(chunk_text_value, overlap)
                current_sentences = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(" ".join(current_sentences))
            else:
                current_sentences.append(sentence)
                current_length = len(" ".join(current_sentences))

        if current_sentences:
            chunk_text_value = " ".join(current_sentences).strip()
            TextChunker._append_chunk(chunks, normalized_text, chunk_text_value, search_offset, document_metadata)

        return TextChunker._set_total_chunks(chunks)

    @staticmethod
    def chunk_by_section(
        text: str,
        chunk_size: int = 800,
        overlap: int = 100,
        metadata: dict | None = None,
    ) -> list[dict]:
        """Split text by detected section headers before sentence-aware chunking."""

        normalized_text = text.strip()
        if not normalized_text:
            return []

        sections = TextChunker._split_sections(normalized_text)
        if len(sections) <= 1:
            return TextChunker.chunk_text(normalized_text, chunk_size, overlap, metadata)

        all_chunks: list[dict] = []
        search_offset = 0
        document_metadata = dict(metadata or {})

        for section_header, section_text in sections:
            section_metadata = {**document_metadata, "section_header": section_header}
            section_chunks = TextChunker.chunk_text(section_text, chunk_size, overlap, section_metadata)

            for chunk in section_chunks:
                if section_header and not chunk["text"].startswith(section_header):
                    chunk["text"] = f"{section_header}\n{chunk['text']}"

                plain_chunk_text = chunk["text"].replace(f"{section_header}\n", "", 1)
                char_start = normalized_text.find(plain_chunk_text.strip(), search_offset)
                if char_start == -1:
                    char_start = normalized_text.find(section_header, search_offset)
                if char_start == -1:
                    char_start = search_offset

                char_end = char_start + len(plain_chunk_text.strip())
                chunk["char_start"] = char_start
                chunk["char_end"] = char_end
                chunk["chunk_index"] = len(all_chunks)
                all_chunks.append(chunk)
                search_offset = max(search_offset, char_end)

        return TextChunker._set_total_chunks(all_chunks)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count using a simple character-based approximation."""

        return len(text) // 4

    @staticmethod
    def smart_chunk(
        text: str,
        chunk_size: int = 800,
        overlap: int = 100,
        metadata: dict | None = None,
    ) -> list[dict]:
        """Choose section-aware or sentence-only chunking and remove tiny chunks."""

        if TextChunker.SECTION_HEADER_PATTERN.search(text):
            chunks = TextChunker.chunk_by_section(text, chunk_size, overlap, metadata)
        else:
            chunks = TextChunker.chunk_text(text, chunk_size, overlap, metadata)

        filtered_chunks = [chunk for chunk in chunks if len(chunk["text"].strip()) >= 50]
        for index, chunk in enumerate(filtered_chunks):
            chunk["chunk_index"] = index
        return TextChunker._set_total_chunks(filtered_chunks)

    @staticmethod
    def add_document_context(chunks: list[dict], doc_name: str, doc_id: str) -> list[dict]:
        """Add document metadata and a document-name prefix to every chunk."""

        for chunk in chunks:
            chunk_metadata = dict(chunk.get("metadata") or {})
            chunk_metadata["doc_name"] = doc_name
            chunk_metadata["doc_id"] = doc_id
            chunk["metadata"] = chunk_metadata
            chunk["text"] = f"Document: {doc_name}\n{chunk['text']}"
        return chunks
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect Hindi vs English using the share of Devanagari characters."""

        if not text:
            return "en"
        devanagari_count = sum(1 for char in text if "\u0900" <= char <= "\u097F")
        total_chars = max(len(text), 1)
        return "hi" if devanagari_count / total_chars > 0.10 else "en"

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences while keeping sentence-ending punctuation."""

        sentences = [sentence.strip() for sentence in TextChunker.SENTENCE_SPLIT_PATTERN.split(text)]
        return [sentence for sentence in sentences if sentence]

    @staticmethod
    def _split_sections(text: str) -> list[tuple[str, str]]:
        """Split text into section header and section body pairs."""

        matches = list(TextChunker.SECTION_HEADER_PATTERN.finditer(text))
        if not matches:
            return []

        sections: list[tuple[str, str]] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[start:end].strip()
            lines = section.splitlines()
            header = lines[0].strip() if lines else ""
            sections.append((header, section))
        return sections

    @staticmethod
    def _append_chunk(
        chunks: list[dict],
        source_text: str,
        chunk_text: str,
        search_offset: int,
        metadata: dict,
    ) -> None:
        """Append a chunk with source character offsets."""

        char_start = source_text.find(chunk_text, search_offset)
        if char_start == -1:
            char_start = source_text.find(chunk_text.strip(), search_offset)
        if char_start == -1:
            char_start = search_offset

        char_end = char_start + len(chunk_text)
        chunks.append(
            {
                "chunk_id": str(uuid4()),
                "text": chunk_text,
                "char_start": char_start,
                "char_end": char_end,
                "chunk_index": len(chunks),
                "total_chunks": 0,
                "metadata": dict(metadata),
            }
        )

    @staticmethod
    def _next_search_offset(source_text: str, chunk_text: str, current_offset: int) -> int:
        """Return the next search offset after a saved chunk."""

        char_start = source_text.find(chunk_text, current_offset)
        if char_start == -1:
            return current_offset
        return char_start + len(chunk_text)

    @staticmethod
    def _get_overlap_text(text: str, overlap: int) -> str:
        """Return the final overlap characters from a chunk."""

        if overlap <= 0:
            return ""
        return text[-overlap:].strip()

    @staticmethod
    def _set_total_chunks(chunks: list[dict]) -> list[dict]:
        """Set total chunk counts on all chunks."""

        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks
        return chunks


