from typing import Any

from app.tools.base import EnterpriseTool


class SlackNotificationTool(EnterpriseTool):
    name = "slack.send_notification"

    async def execute(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success",
            "system": "Slack",
            "delivered": True,
            "parameters": parameters,
        }