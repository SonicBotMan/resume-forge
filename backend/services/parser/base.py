"""Base parser interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    @abstractmethod
    async def parse(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def extract_pages(self) -> List[Dict[str, Any]]:
        pass
