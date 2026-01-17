"""
Workflow Builder Service
Generates n8n workflow JSON from templates with user-specific customization
"""
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from copy import deepcopy

from app.services.n8n_client import N8nClient
from app.models.workflow import WorkflowTemplate, UserWorkflow
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """
    Builds complete n8n workflows from templates
    Handles credential injection, parameter substitution, and n8n API interaction
    """

    def __init__(self):
        self.n8n = N8nClient()

    async def build_from_template(
        self,
        template: WorkflowTemplate,
        user_id: str,
        inputs: Dict[str, Any],
        custom_name: Optional[str] = None,
        db: Optional[SessionLocal] = None
    ) -> UserWorkflow:
        """
        Build workflow from template with user inputs

        Args:
            template: WorkflowTemplate instance
            user_id: User ID for workflow ownership
            inputs: User-provided configuration values
            custom_name: Optional custom workflow name

        Returns:
            UserWorkflow: Created workflow record
        """
        try:
            logger.info(f"Building workflow from template {template.id} for user {user_id}")

            # Validate inputs against template requirements
            self._validate_inputs(template, inputs)

            # Generate workflow JSON
            workflow_json = self._generate_workflow_json(
                template=template,
                user_id=user_id,
                inputs=inputs,
                custom_name=custom_name
            )

            # Create workflow in n8n
            n8n_workflow = await self.n8n.create_workflow(workflow_json)
            n8n_workflow_id = n8n_workflow['id']

            # Activate workflow
            await self.n8n.activate_workflow(n8n_workflow_id)

            # Generate webhook URL
            webhook_url = self.n8n.build_webhook_url(user_id, n8n_workflow_id)

            # Save to database
            should_close = False
            if db is None:
                db = SessionLocal()
                should_close = True

            try:
                user_workflow = UserWorkflow(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    template_id=str(template.id),
                    n8n_workflow_id=n8n_workflow_id,
                    name=workflow_json['name'],
                    status='active',
                    webhook_url=webhook_url,
                    configuration=inputs,
                    created_at=datetime.utcnow()
                )

                db.add(user_workflow)
                db.commit()
                db.refresh(user_workflow)

                logger.info(f"Workflow created successfully: {user_workflow.id}")
                return user_workflow

            finally:
                if should_close:
                    db.close()

        except Exception as e:
            logger.error(f"Workflow build failed: {str(e)}", exc_info=True)
            # Cleanup: try to delete n8n workflow if created
            if 'n8n_workflow_id' in locals():
                try:
                    await self.n8n.delete_workflow(n8n_workflow_id)
                except:
                    pass
            raise

    def _validate_inputs(self, template: WorkflowTemplate, inputs: Dict[str, Any]):
        """
        Validate user inputs against template requirements
        """
        # Check required inputs
        for req_input in template.required_inputs:
            field_name = req_input['name']
            if field_name not in inputs or inputs[field_name] is None:
                raise ValueError(f"Required input '{field_name}' is missing")

            # Type validation
            if req_input['type'] == 'number':
                try:
                    inputs[field_name] = float(inputs[field_name])
                except (ValueError, TypeError):
                    raise ValueError(f"Input '{field_name}' must be a number")

            # Range validation for numbers
            if req_input['type'] == 'number':
                if 'min' in req_input and inputs[field_name] < req_input['min']:
                    raise ValueError(f"Input '{field_name}' must be >= {req_input['min']}")
                if 'max' in req_input and inputs[field_name] > req_input['max']:
                    raise ValueError(f"Input '{field_name}' must be <= {req_input['max']}")

            # Options validation for select fields
            if 'options' in req_input:
                valid_options = [opt if isinstance(opt, str) else opt['value']
                               for opt in req_input['options']]
                if inputs[field_name] not in valid_options:
                    raise ValueError(f"Input '{field_name}' must be one of: {valid_options}")

        # Apply defaults for optional inputs
        for opt_input in template.optional_inputs or []:
            field_name = opt_input['name']
            if field_name not in inputs or inputs[field_name] is None:
                inputs[field_name] = opt_input.get('default')

    def _generate_workflow_json(
        self,
        template: WorkflowTemplate,
        user_id: str,
        inputs: Dict[str, Any],
        custom_name: Optional[str] = None
    ) -> Dict:
        """
        Generate complete n8n workflow JSON with user-specific values
        """
        # Deep copy template JSON
        workflow_json = deepcopy(template.n8n_json)

        # Generate unique workflow name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        workflow_name = custom_name or f"{template.name}_{user_id[:8]}_{timestamp}"
        workflow_json['name'] = workflow_name

        # Inject user context into all nodes
        replacements = {
            'user_id': user_id,
            'workflow_name': workflow_name,
            'timestamp': timestamp,
            **inputs
        }

        # Process all nodes
        for node in workflow_json.get('nodes', []):
            # Replace placeholders in parameters
            if 'parameters' in node:
                node['parameters'] = self._replace_placeholders(
                    node['parameters'],
                    replacements
                )

            # Handle credential injection
            if 'credentials' in node:
                node['credentials'] = self._inject_credentials(
                    node['credentials'],
                    user_id
                )

            # Update webhook URLs
            if node.get('type') == 'n8n-nodes-base.webhook':
                if 'parameters' in node and 'path' in node['parameters']:
                    # Set unique webhook path
                    node['parameters']['path'] = f"{user_id}/{workflow_name}"

        return workflow_json

    def _replace_placeholders(self, obj: Any, replacements: Dict[str, Any]) -> Any:
        """
        Recursively replace {{placeholder}} patterns in workflow JSON
        """
        if isinstance(obj, str):
            # Replace all {{key}} patterns
            result = obj
            for key, value in replacements.items():
                pattern = f"{{{{{key}}}}}"
                if pattern in result:
                    # If entire string is just the placeholder, replace with typed value
                    if result == pattern:
                        return value
                    # Otherwise do string replacement
                    result = result.replace(pattern, str(value))
            return result

        elif isinstance(obj, dict):
            return {k: self._replace_placeholders(v, replacements) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._replace_placeholders(item, replacements) for item in obj]

        else:
            return obj

    def _inject_credentials(self, credentials: List[Dict], user_id: str) -> List[Dict]:
        """
        Inject user-specific credential IDs
        In production, credentials should be stored securely per user
        """
        updated_credentials = []

        for cred in credentials:
            # Generate user-specific credential ID
            cred_type = cred.get('type', '')
            cred_id = f"{cred_type}_user_{user_id}"

            updated_credentials.append({
                **cred,
                'id': cred_id
            })

        return updated_credentials

    async def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> UserWorkflow:
        """
        Update existing workflow configuration
        """
        db = SessionLocal()
        try:
            # Get workflow
            workflow = db.query(UserWorkflow).filter(UserWorkflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Get template
            template = db.query(WorkflowTemplate).filter(
                WorkflowTemplate.id == workflow.template_id
            ).first()

            # Merge updates with existing config
            new_config = {**workflow.configuration, **updates}

            # Validate
            self._validate_inputs(template, new_config)

            # Regenerate workflow JSON
            workflow_json = self._generate_workflow_json(
                template=template,
                user_id=workflow.user_id,
                inputs=new_config,
                custom_name=workflow.name
            )

            # Update in n8n
            await self.n8n.update_workflow(workflow.n8n_workflow_id, workflow_json)

            # Update database
            workflow.configuration = new_config
            workflow.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(workflow)

            return workflow

        finally:
            db.close()

    async def delete_workflow(self, workflow_id: str):
        """
        Delete workflow from both n8n and database
        """
        db = SessionLocal()
        try:
            workflow = db.query(UserWorkflow).filter(UserWorkflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Delete from n8n
            try:
                await self.n8n.delete_workflow(workflow.n8n_workflow_id)
            except Exception as e:
                logger.warning(f"Failed to delete n8n workflow: {str(e)}")

            # Delete from database
            db.delete(workflow)
            db.commit()

            logger.info(f"Workflow {workflow_id} deleted successfully")

        finally:
            db.close()

    async def toggle_workflow_status(self, workflow_id: str, active: bool) -> UserWorkflow:
        """
        Activate or deactivate workflow
        """
        db = SessionLocal()
        try:
            workflow = db.query(UserWorkflow).filter(UserWorkflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Update n8n
            if active:
                await self.n8n.activate_workflow(workflow.n8n_workflow_id)
                workflow.status = 'active'
            else:
                await self.n8n.deactivate_workflow(workflow.n8n_workflow_id)
                workflow.status = 'paused'

            workflow.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(workflow)

            return workflow

        finally:
            db.close()
