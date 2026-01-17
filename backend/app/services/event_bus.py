"""
Event Bus
Decouples system components using an Event-Driven Architecture.
Implements 2026 best practices for scalability and async processing.
"""
import json
import logging
from typing import Dict, Any, Callable, Awaitable
from app.services.cache import redis_client

logger = logging.getLogger(__name__)

class EventBus:
    """
    Message-broker interface for platform-wide events.
    Uses Redis as the primary transport.
    """

    def __init__(self):
        self.stream_name = "platform_events"

    async def publish(self, event_type: str, data: Dict[str, Any]):
        """
        Publishes an event to the bus.
        """
        event = {
            "type": event_type,
            "payload": json.dumps(data)
        }
        try:
            if redis_client:
                await redis_client.xadd(self.stream_name, event)
                logger.info(f"Published event: {event_type}")
            else:
                logger.warning(f"Redis not available, event {event_type} not published")
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")

    async def subscribe(self, callback: Callable[[str, Dict[str, Any]], Awaitable[None]]):
        """
        Subscribes to events (simplified version for worker implementation).
        """
        if not redis_client:
            return

        logger.info("Subscribed to platform events")
        last_id = "$"

        while True:
            try:
                events = await redis_client.xread({self.stream_name: last_id}, count=1, block=5000)
                for stream, message_list in events:
                    for message_id, message_data in message_list:
                        event_type = message_data.get("type")
                        payload = json.loads(message_data.get("payload", "{}"))
                        await callback(event_type, payload)
                        last_id = message_id
            except Exception as e:
                logger.error(f"Error reading from event bus: {e}")
                break

event_bus = EventBus()
