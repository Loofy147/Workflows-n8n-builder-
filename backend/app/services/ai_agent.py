"""
AI Workflow Builder Agent
Handles conversation with users, understands intent, matches templates, generates workflows
Optimized for cost efficiency using hybrid AI approach
"""
from anthropic import Anthropic, AsyncAnthropic
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from app.config import settings
from app.services.template_matcher import TemplateMatcher
from app.services.cost_estimator import CostEstimator
from app.utils.algeria_utils import normalize_darja, validate_wilaya
from app.metrics import AI_TOKEN_USAGE

logger = logging.getLogger(__name__)


class AIWorkflowAgent:
    """
    Main AI agent that interprets user requests and builds workflows.
    Enhanced for 2026 with role-based personas, tool tracing, and MAS compatibility.
    """

    def __init__(self, role: str = "general"):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.template_matcher = TemplateMatcher()
        self.cost_estimator = CostEstimator()
        self.role = role
        self.conversation_memory = {}  # In-memory cache, replace with Redis in prod

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        db: Optional[Any] = None,
        orchestrator_state: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user messages

        Returns:
            dict: Response containing message, workflow data, or clarification questions
        """
        try:
            # 2026 Tracing
            if orchestrator_state:
                orchestrator_state.trace.append(f"Agent {self.role} started processing.")

            # Get conversation history
            history = self._get_conversation_history(conversation_id, db=db) if conversation_id else []

            # Get user context
            user_context = await self._get_user_context(user_id, db=db)

            # Build system prompt with templates and context
            system_prompt = self._build_system_prompt(user_context)

            # Build conversation messages
            messages = self._build_messages(history, message)

            # Call Claude API
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                system=system_prompt,
                messages=messages,
                temperature=0.3  # Lower temperature for more consistent outputs
            )

            if orchestrator_state:
                orchestrator_state.trace.append(f"Agent {self.role} received response from LLM.")

            # Parse response
            agent_response = self._parse_agent_response(response.content[0].text)

            # Track token usage for cost monitoring
            self._track_token_usage(response.usage, user_id)

            # Save conversation
            if conversation_id:
                self._save_conversation(conversation_id, message, agent_response)

            # Handle different response types
            if agent_response['type'] == 'clarification':
                return await self._handle_clarification(agent_response, user_id)

            elif agent_response['type'] == 'workflow_ready':
                return await self._handle_workflow_creation(agent_response, user_id)

            elif agent_response['type'] == 'error':
                return await self._handle_error(agent_response)

            else:
                # Simple response
                return {
                    "type": "message",
                    "content": agent_response.get('message', ''),
                    "suggestions": agent_response.get('suggestions', [])
                }

        except Exception as e:
            logger.error(f"AI Agent error: {str(e)}", exc_info=True)
            return {
                "type": "error",
                "message": "Désolé, une erreur s'est produite. Veuillez réessayer.",
                "error_code": "AGENT_ERROR"
            }

    def _build_system_prompt(self, user_context: Dict) -> str:
        """Build comprehensive system prompt with user context, templates, and role-based personas"""

        # Load available templates
        templates = self.template_matcher.get_all_templates()
        # Filter templates based on role if necessary
        templates_json = json.dumps([t.to_dict() for t in templates], ensure_ascii=False)

        role_personas = {
            "sales": "You are a Sales Automation Expert focused on lead generation and CRM integration in Algeria (Ouedkniss, social media).",
            "logistics": "You are a Logistics Specialist focused on delivery automation and order tracking (Yalidine, local transport).",
            "finance": "You are a Fintech Advisor focused on payment tracking and invoice automation (Baridimob, CCP, CCP payment verification).",
            "general": "You are a General Automation Architect for Algerian businesses."
        }

        persona = role_personas.get(self.role, role_personas["general"])

        prompt = f"""{persona}

You are an AI Workflow Builder Agent for an automation platform serving Algerian businesses.

USER CONTEXT:
- User ID: {user_context['user_id']}
- Tier: {user_context['tier']}
- Credits: {user_context['credits']} DZD
- Location: {user_context.get('location', 'Algeria')}
- Language preference: {user_context.get('language', 'Darja/French')}

AVAILABLE WORKFLOW TEMPLATES:
{templates_json}

YOUR TASK:
1. Understand what automation the user needs (in Darja, French, or English)
2. Match their request to the best template OR determine if custom workflow needed
3. Ask ONLY essential questions (max 3-4 questions)
4. Provide accurate cost estimate BEFORE building
5. When ready, generate workflow configuration

ALGERIA-SPECIFIC RULES:
- Validate wilaya codes (01-58)
- Phone format: +213 5XX/6XX/7XX
- Business hours: Sunday-Thursday 8AM-5PM
- Use Darja for customer-facing content when appropriate
- Know local platforms: Ouedkniss, Yalidine, CCP, Baridimob

RESPONSE FORMAT (JSON):
For clarification:
{{
  "type": "clarification",
  "message": "User-friendly question in their language",
  "questions": [
    {{
      "field": "category",
      "question": "Quelle catégorie de produits?",
      "options": ["Electronics", "Fashion", "Real Estate"],
      "required": true
    }}
  ],
  "template_match": "template_id",
  "confidence": 0.85
}}

For workflow ready:
{{
  "type": "workflow_ready",
  "message": "✅ Votre workflow est prêt!",
  "template_id": "template_id",
  "inputs": {{
    "category": "Electronics",
    "location": "16",
    "keywords": ["Samsung", "iPhone"]
  }},
  "estimated_cost_dzd": 8.00,
  "execution_time_seconds": 45
}}

For simple response:
{{
  "type": "message",
  "message": "Your helpful response here",
  "suggestions": ["Try lead generation", "Automate customer support"]
}}

IMPORTANT:
- Always respond in the user's language (detect from message)
- Be concise - avoid long explanations
- Provide cost BEFORE asking for confirmation
- Never expose technical details (n8n, JSON, APIs)
- Focus on business value, not technical implementation
"""
        return prompt

    def _build_messages(self, history: List[Dict], new_message: str) -> List[Dict]:
        """Build conversation messages for Claude API"""
        messages = []

        # Add history
        for h in history:
            messages.append({
                "role": h['role'],
                "content": h['content']
            })

        # Add new user message
        messages.append({
            "role": "user",
            "content": new_message
        })

        return messages

    def _parse_agent_response(self, response_text: str) -> Dict:
        """Parse agent's JSON response with error handling"""
        try:
            # Try to extract JSON from response
            # Claude sometimes wraps JSON in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.error(f"Response text: {response_text}")

            # Fallback: return as simple message
            return {
                "type": "message",
                "message": response_text
            }

    async def _handle_clarification(self, response: Dict, user_id: str) -> Dict:
        """Handle clarification questions from agent"""
        return {
            "type": "clarification",
            "message": response['message'],
            "questions": response['questions'],
            "template_match": response.get('template_match'),
            "confidence": response.get('confidence', 0.0)
        }

    async def _handle_workflow_creation(self, response: Dict, user_id: str) -> Dict:
        """Handle workflow creation when agent has all info"""
        from app.services.workflow_builder import WorkflowBuilder

        try:
            # Get template
            template = self.template_matcher.get_template(response['template_id'])
            if not template:
                raise ValueError(f"Template {response['template_id']} not found")

            # Build workflow
            builder = WorkflowBuilder()
            workflow = await builder.build_from_template(
                template=template,
                user_id=user_id,
                inputs=response['inputs']
            )

            # Generate activation form
            activation_form = self._generate_activation_form(template, response['inputs'])

            return {
                "type": "workflow_ready",
                "message": response['message'],
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "webhook_url": workflow.webhook_url
                },
                "activation_form": activation_form,
                "estimated_cost": response['estimated_cost_dzd'],
                "execution_time": response['execution_time_seconds']
            }

        except Exception as e:
            logger.error(f"Workflow creation failed: {str(e)}", exc_info=True)
            return {
                "type": "error",
                "message": "Impossible de créer le workflow. Veuillez réessayer.",
                "error": str(e)
            }

    def _generate_activation_form(self, template: Any, filled_inputs: Dict) -> Dict:
        """Generate activation form with pre-filled values"""
        form = {
            "title": template.name,
            "description": template.description,
            "fields": []
        }

        # Add required inputs
        for req_input in template.required_inputs:
            field = {
                "name": req_input['name'],
                "label": req_input['label'],
                "type": req_input['type'],
                "required": True,
                "value": filled_inputs.get(req_input['name'], req_input.get('default'))
            }

            if 'options' in req_input:
                field['options'] = req_input['options']

            form['fields'].append(field)

        # Add optional inputs
        for opt_input in template.optional_inputs or []:
            field = {
                "name": opt_input['name'],
                "label": opt_input['label'],
                "type": opt_input['type'],
                "required": False,
                "value": filled_inputs.get(opt_input['name'], opt_input.get('default'))
            }

            if 'options' in opt_input:
                field['options'] = opt_input['options']

            form['fields'].append(field)

        return form

    async def _get_user_context(self, user_id: str, db: Optional[Any] = None) -> Dict:
        """Fetch user context from database"""
        from app.db.session import SessionLocal
        from app.models.user import User

        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            return {
                "user_id": user.id,
                "tier": user.tier,
                "credits": float(user.credits_dzd),
                "location": user.location or "Algeria",
                "language": user.language_preference or "fr"
            }
        finally:
            if should_close:
                db.close()

    def _get_conversation_history(self, conversation_id: str, db: Optional[Any] = None) -> List[Dict]:
        """Get conversation history from cache or database"""
        # Check memory cache first
        if conversation_id in self.conversation_memory:
            return self.conversation_memory[conversation_id]

        # Fallback to database
        from app.db.session import SessionLocal
        from app.models.workflow import ChatConversation

        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            conv = db.query(ChatConversation).filter(
                ChatConversation.id == conversation_id
            ).first()

            if conv and conv.messages:
                return conv.messages

            return []
        finally:
            if should_close:
                db.close()

    def _save_conversation(self, conversation_id: str, user_message: str, agent_response: Dict):
        """Save conversation turn to memory and database"""
        # Update memory cache
        if conversation_id not in self.conversation_memory:
            self.conversation_memory[conversation_id] = []

        self.conversation_memory[conversation_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": json.dumps(agent_response, ensure_ascii=False)}
        ])

        # Async save to database (don't wait)
        # In production, use background task or message queue

    def _track_token_usage(self, usage: Any, user_id: str):
        """Track AI token usage for cost monitoring"""
        logger.info(f"Token usage for user {user_id}: {usage.input_tokens} in, {usage.output_tokens} out")

        # Calculate cost
        input_cost = (usage.input_tokens / 1_000_000) * 3.0  # $3 per 1M tokens
        output_cost = (usage.output_tokens / 1_000_000) * 15.0  # $15 per 1M tokens
        total_cost_usd = input_cost + output_cost

        # Convert to DZD (approx 135 DZD = 1 USD)
        total_cost_dzd = total_cost_usd * 135

        logger.info(f"Estimated cost: {total_cost_dzd:.4f} DZD")

        # Update metrics
        AI_TOKEN_USAGE.labels(model="claude-3-5-sonnet").inc(usage.input_tokens + usage.output_tokens)

    async def _handle_error(self, response: Dict) -> Dict:
        """Handle error responses from agent"""
        return {
            "type": "error",
            "message": response.get('message', 'Une erreur s\'est produite'),
            "error_code": response.get('error_code', 'UNKNOWN')
        }
