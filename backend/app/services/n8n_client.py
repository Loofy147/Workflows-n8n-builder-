"""
n8n API Client
Handles all interactions with n8n instance with proper error handling and retry logic
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from app.config import settings
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class N8nClientError(Exception):
    """Base exception for n8n client errors"""
    pass


class N8nClient:
    """
    Async client for n8n API operations
    Implements retry logic, circuit breaker, and graceful degradation
    """

    def __init__(self):
        self.base_url = settings.N8N_API_URL
        self.api_key = settings.N8N_API_KEY
        self.webhook_base_url = settings.N8N_WEBHOOK_URL
        self.session: Optional[aiohttp.ClientSession] = None

        # Circuit breaker state
        self.failure_count = 0
        self.circuit_open = False
        self.last_failure_time = None
        self.circuit_timeout = 60  # seconds

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "X-N8N-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _check_circuit_breaker(self):
        """Check if circuit breaker allows requests"""
        if not self.circuit_open:
            return True

        # Check if timeout has passed
        if self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed > self.circuit_timeout:
                logger.info("Circuit breaker closed after timeout")
                self.circuit_open = False
                self.failure_count = 0
                return True

        raise N8nClientError("Circuit breaker open - n8n service unavailable")

    def _record_success(self):
        """Record successful request"""
        self.failure_count = 0
        if self.circuit_open:
            logger.info("Circuit breaker closed after successful request")
            self.circuit_open = False

    def _record_failure(self):
        """Record failed request and update circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= 5:
            logger.error("Opening circuit breaker after 5 failures")
            self.circuit_open = True

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 3
    ) -> Dict:
        """
        Make HTTP request to n8n API with retry logic
        """
        self._check_circuit_breaker()

        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()

        for attempt in range(retry_count):
            try:
                async with session.request(method, url, json=data, params=params) as response:
                    if response.status == 200:
                        self._record_success()
                        return await response.json()

                    elif response.status == 401:
                        raise N8nClientError("n8n API authentication failed")

                    elif response.status == 404:
                        raise N8nClientError(f"n8n endpoint not found: {endpoint}")

                    elif response.status >= 500:
                        error_text = await response.text()
                        logger.warning(f"n8n server error (attempt {attempt + 1}/{retry_count}): {error_text}")

                        if attempt < retry_count - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            self._record_failure()
                            raise N8nClientError(f"n8n server error: {error_text}")

                    else:
                        error_text = await response.text()
                        raise N8nClientError(f"n8n API error {response.status}: {error_text}")

            except aiohttp.ClientError as e:
                logger.error(f"Network error calling n8n (attempt {attempt + 1}/{retry_count}): {str(e)}")

                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    self._record_failure()
                    raise N8nClientError(f"Network error: {str(e)}")

    async def health_check(self) -> bool:
        """Check if n8n instance is healthy"""
        try:
            await self._make_request("GET", "/workflows", retry_count=1)
            return True
        except Exception as e:
            logger.error(f"n8n health check failed: {str(e)}")
            return False

    async def create_workflow(self, workflow_json: Dict) -> Dict:
        """
        Create new workflow in n8n

        Args:
            workflow_json: Complete n8n workflow definition

        Returns:
            dict: Created workflow with id
        """
        logger.info(f"Creating workflow: {workflow_json.get('name')}")

        try:
            result = await self._make_request("POST", "/workflows", data=workflow_json)
            logger.info(f"Workflow created: {result.get('id')}")
            return result

        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}", exc_info=True)
            raise N8nClientError(f"Workflow creation failed: {str(e)}")

    async def update_workflow(self, workflow_id: str, workflow_json: Dict) -> Dict:
        """
        Update existing workflow
        """
        logger.info(f"Updating workflow: {workflow_id}")

        try:
            result = await self._make_request(
                "PATCH",
                f"/workflows/{workflow_id}",
                data=workflow_json
            )
            logger.info(f"Workflow updated: {workflow_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {str(e)}")
            raise N8nClientError(f"Workflow update failed: {str(e)}")

    async def activate_workflow(self, workflow_id: str) -> Dict:
        """
        Activate workflow (enable triggers)
        """
        logger.info(f"Activating workflow: {workflow_id}")

        try:
            result = await self._make_request(
                "PATCH",
                f"/workflows/{workflow_id}/activate",
                data={"active": True}
            )
            logger.info(f"Workflow activated: {workflow_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {str(e)}")
            raise N8nClientError(f"Workflow activation failed: {str(e)}")

    async def deactivate_workflow(self, workflow_id: str) -> Dict:
        """
        Deactivate workflow
        """
        logger.info(f"Deactivating workflow: {workflow_id}")

        try:
            result = await self._make_request(
                "PATCH",
                f"/workflows/{workflow_id}/activate",
                data={"active": False}
            )
            logger.info(f"Workflow deactivated: {workflow_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to deactivate workflow {workflow_id}: {str(e)}")
            raise N8nClientError(f"Workflow deactivation failed: {str(e)}")

    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete workflow permanently
        """
        logger.info(f"Deleting workflow: {workflow_id}")

        try:
            await self._make_request("DELETE", f"/workflows/{workflow_id}")
            logger.info(f"Workflow deleted: {workflow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {str(e)}")
            raise N8nClientError(f"Workflow deletion failed: {str(e)}")

    async def get_workflow(self, workflow_id: str) -> Dict:
        """
        Get workflow details
        """
        try:
            return await self._make_request("GET", f"/workflows/{workflow_id}")
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {str(e)}")
            raise N8nClientError(f"Failed to retrieve workflow: {str(e)}")

    async def list_workflows(self, active_only: bool = False) -> List[Dict]:
        """
        List all workflows
        """
        try:
            params = {"active": "true"} if active_only else None
            result = await self._make_request("GET", "/workflows", params=params)
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            raise N8nClientError(f"Failed to list workflows: {str(e)}")

    async def trigger_workflow(self, workflow_id: str, data: Dict) -> Dict:
        """
        Manually trigger workflow execution.
        2026: Publishes an event before triggering.
        """
        await event_bus.publish("workflow_trigger_requested", {
            "workflow_id": workflow_id,
            "data": data
        })

        logger.info(f"Triggering workflow: {workflow_id}")

        try:
            # Get workflow to find webhook URL
            workflow = await self.get_workflow(workflow_id)

            # Find webhook node
            webhook_url = None
            for node in workflow.get("nodes", []):
                if node.get("type") == "n8n-nodes-base.webhook":
                    webhook_path = node.get("parameters", {}).get("path", "")
                    webhook_url = f"{self.webhook_base_url}/{webhook_path}"
                    break

            if not webhook_url:
                raise N8nClientError("Workflow has no webhook trigger")

            # Trigger via webhook
            session = await self._get_session()
            async with session.post(webhook_url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise N8nClientError(f"Webhook trigger failed: {error_text}")

        except Exception as e:
            logger.error(f"Failed to trigger workflow {workflow_id}: {str(e)}")
            raise N8nClientError(f"Workflow trigger failed: {str(e)}")

    async def get_execution(self, execution_id: str) -> Dict:
        """
        Get execution details
        """
        try:
            return await self._make_request("GET", f"/executions/{execution_id}")
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {str(e)}")
            raise N8nClientError(f"Failed to retrieve execution: {str(e)}")

    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        List workflow executions
        """
        try:
            params = {"limit": limit}
            if workflow_id:
                params["workflowId"] = workflow_id

            result = await self._make_request("GET", "/executions", params=params)
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list executions: {str(e)}")
            raise N8nClientError(f"Failed to list executions: {str(e)}")

    async def delete_execution(self, execution_id: str) -> bool:
        """
        Delete execution record
        """
        try:
            await self._make_request("DELETE", f"/executions/{execution_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete execution {execution_id}: {str(e)}")
            return False

    def build_webhook_url(self, user_id: str, workflow_id: str) -> str:
        """
        Generate webhook URL for workflow
        """
        return f"{self.webhook_base_url}/{user_id}/{workflow_id}"
