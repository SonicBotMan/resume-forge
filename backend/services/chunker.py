"""Text chunking service."""

import re
from typing import List, Dict, Any


class Chunker:
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 1500):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_by_document_structure(
        self, parsed_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        chunks = []
        file_name = parsed_doc.get("file_name", "")
        pages = parsed_doc.get("pages", [])

        for page in pages:
            page_num = page.get("page_num", 0)
            content = page.get("content", "")

            page_chunks = self._split_content(content, page_num, file_name)
            chunks.extend(page_chunks)

        return self._merge_short_chunks(chunks)

    def _split_content(
        self, content: str, page_num: int, file_name: str
    ) -> List[Dict[str, Any]]:
        paragraphs = re.split(r"\n\n+", content)
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": "\n\n".join(current_chunk),
                        "source_file": file_name,
                        "page_num": page_num,
                    }
                )
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append(
                {
                    "content": "\n\n".join(current_chunk),
                    "source_file": file_name,
                    "page_num": page_num,
                }
            )

        return chunks

    def _merge_short_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        merged = []
        current = chunks[0].copy()

        for next_chunk in chunks[1:]:
            if len(current["content"]) < self.min_chunk_size:
                current["content"] += "\n\n" + next_chunk["content"]
                current["page_num"] = next_chunk["page_num"]
            else:
                merged.append(current)
                current = next_chunk.copy()

        merged.append(current)
        return merged

    def remove_noise(self, text: str) -> str:
        text = re.sub(r"Page \d+", "", text)
        text = re.sub(r"感谢观看|谢谢|EOF|~{10,}", "", text)
        text = re.sub(r"\.{5,}", "", text)
        return text.strip()
