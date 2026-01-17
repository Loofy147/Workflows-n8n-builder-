"""
Event Processor Worker
Consumes events from the bus and executes background logic.
Essential for 2026 event-driven architecture.
"""
import asyncio
import logging
from app.services.event_bus import event_bus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_event(event_type: str, payload: dict):
    """
    Dispatcher for event processing.
    """
    logger.info(f"Processing event: {event_type} with payload: {payload}")

    if event_type == "workflow_created":
        # Handle post-creation tasks (e.g. logging to audit, notifying user)
        logger.info(f"Audit: Workflow {payload.get('workflow_id')} registered in audit logs.")

    elif event_type == "workflow_trigger_requested":
        logger.info(f"Async Execution: Preparing trigger for workflow {payload.get('workflow_id')}")

async def main():
    logger.info("Event Processor Worker starting...")
    await event_bus.subscribe(process_event)

if __name__ == "__main__":
    asyncio.run(main())
