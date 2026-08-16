from typing import Any

from app.core.config import settings
from app.tools.base import EnterpriseTool


class SalesforceCreateCustomerTool(EnterpriseTool):
    name = "salesforce.create_customer"

    def __init__(self) -> None:
        self.mode = settings.salesforce_mode.lower()

    async def execute(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if self.mode == "mock":
            return self._execute_mock(parameters)

        if self.mode == "mule":
            return await self._execute_mule(parameters)

        raise ValueError(
            f"Unsupported Salesforce mode: {self.mode}"
        )

    @staticmethod
    def _execute_mock(
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "success",
            "system": "Salesforce",
            "integration_mode": "mock",
            "customer_id": "SF-10001",
            "parameters": parameters,
        }

    async def _execute_mule(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if not settings.mule_experience_api_url:
            raise RuntimeError(
                "MuleSoft Experience API URL is not configured"
            )

        raise NotImplementedError(
            "MuleSoft Experience API integration "
            "has not been enabled yet"
        )