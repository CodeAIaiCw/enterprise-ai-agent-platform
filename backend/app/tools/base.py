from abc import ABC, abstractmethod
from typing import Any


class EnterpriseTool(ABC):
    name: str

    @abstractmethod
    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError