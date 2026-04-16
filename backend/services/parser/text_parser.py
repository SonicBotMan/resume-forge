"""Text parser for plain text and markdown files."""

import asyncio
from typing import Dict, Any


class TextParser:
    async def parse(self, file_path: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._parse_sync, file_path)

    def _parse_sync(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.split("\n")
        sections = []
        current_section = {"title": "", "content": []}

        for line in lines:
            if line.strip().startswith("#") and not line.strip().startswith("##"):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"title": line.strip(), "content": []}
            else:
                current_section["content"].append(line)

        if current_section["content"]:
            sections.append(current_section)

        full_content = "\n".join(
            [
                s["content"]
                if isinstance(s["content"], str)
                else "\n".join(s["content"])
                for s in sections
            ]
        )

        return {
            "file_name": file_path.split("/")[-1],
            "file_type": "text",
            "pages": [
                {
                    "page_num": 1,
                    "content": full_content,
                    "metadata": {"sections": sections},
                }
            ],
            "total_chars": len(content),
        }
