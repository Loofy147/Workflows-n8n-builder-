"""
Event Processor Worker
Consumes events from the bus and executes background logic.
Essential for 2026 event-driven architecture.
"""
import asyncio
import logging
import json
from app.services.event_bus import event_bus
from app.services.sbom_generator import sbom_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_event(event_type: str, payload: dict):
    """
    Dispatcher for event processing.
    """
    logger.info(f"Processing event: {event_type} with payload: {payload}")

    if event_type == "workflow_created":
        # 2026 Architectural Requirement: SBOM Generation
        logger.info(f"Generating SBOM for Workflow {payload.get('workflow_id')}...")
        sbom = sbom_generator.generate(
            workflow_id=payload.get('workflow_id'),
            user_id=payload.get('user_id'),
            template_id=payload.get('template_id'),
            n8n_id=payload.get('n8n_id')
        )
        logger.info(f"SBOM Generated: {json.dumps(sbom, indent=2)}")

        # Handle post-creation tasks (e.g. logging to audit, notifying user)
        logger.info(f"Audit: Workflow {payload.get('workflow_id')} registered in audit logs.")

    elif event_type == "workflow_trigger_requested":
        logger.info(f"Async Execution: Preparing trigger for workflow {payload.get('workflow_id')}")

async def main():
    logger.info("Event Processor Worker starting...")
    await event_bus.subscribe(process_event)

if __name__ == "__main__":
    asyncio.run(main())
