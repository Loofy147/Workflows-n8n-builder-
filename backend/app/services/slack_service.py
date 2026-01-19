"""
Slack Integration Service
Provides common tools for sending notifications and alerts to Slack channels.
"""
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SlackService:
    """
    Service for interacting with Slack Webhooks.
    """

    async def send_message(self, webhook_url: str, text: str, blocks: Optional[list] = None) -> bool:
        """
        Sends a message to a Slack channel via webhook.
        """
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    def build_alert_block(self, title: str, details: Dict[str, Any]) -> list:
        """
        Helper to build structured alert blocks.
        """
        fields = []
        for key, value in details.items():
            fields.append({
                "type": "mrkdwn",
                "text": f"*{key}:* {value}"
            })

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *{title}*"
                }
            },
            {
                "type": "section",
                "fields": fields
            }
        ]

slack_service = SlackService()
