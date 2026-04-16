import asyncio
from typing import Dict, Any
from markitdown import MarkItDown


class MarkItDownParser:
    def __init__(self):
        self._md = MarkItDown()

    async def parse(self, file_path: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._parse_sync, file_path)

    def _parse_sync(self, file_path: str) -> Dict[str, Any]:
        result = self._md.convert(file_path)
        content = result.text_content or ""
        return {
            "file_name": file_path.split("/")[-1],
            "file_type": "markitdown",
            "pages": [
                {
                    "page_num": 1,
                    "content": content,
                    "metadata": {"title": result.title} if result.title else {},
                }
            ],
            "total_chars": len(content),
        }
