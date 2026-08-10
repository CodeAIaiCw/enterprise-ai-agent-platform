from app.tools.salesforce import SalesforceCreateCustomerTool
from app.tools.sap import SAPVerifyCustomerTool
from app.tools.slack import SlackNotificationTool


class ToolRegistry:
    def __init__(self) -> None:
        tools = [
            SalesforceCreateCustomerTool(),
            SAPVerifyCustomerTool(),
            SlackNotificationTool(),
        ]

        self._tools = {
            tool.name: tool
            for tool in tools
        }

    def get(self, name: str):
        return self._tools.get(name)


tool_registry = ToolRegistry()