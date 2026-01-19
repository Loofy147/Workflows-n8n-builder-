import json
import os
from typing import List, Optional, Dict, Any
import logging
from app.models.workflow import WorkflowTemplate
from app.services.cache import redis_client

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

class TemplateMatcher:
    """
    Manages workflow templates and matches user intent to templates
    """

    def __init__(self, templates_dir: Optional[str] = None, db: Optional[Session] = None):
        self.templates_dir = templates_dir or os.getenv("TEMPLATES_DIR", "templates")
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.db = db
        self._load_templates_from_disk()
        # Still load from DB for sync methods if needed,
        # but async methods will use cache
        if db:
            self._load_templates_from_db(db)

    async def get_all_templates_async(self) -> List[WorkflowTemplate]:
        """
        Retrieves all templates with Redis caching.
        """
        cache_key = "all_workflow_templates"

        # Try Redis
        if redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return [WorkflowTemplate(**d) for d in data]
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")

        # Load from DB if session available
        if self.db:
            db_templates = self.db.query(WorkflowTemplate).all()
            for t in db_templates:
                self.templates[t.id] = t

        templates = list(self.templates.values())

        # Store in Redis
        if redis_client:
            try:
                serializable = [t.to_dict() for t in templates]
                await redis_client.setex(cache_key, 3600, json.dumps(serializable))
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")

        return templates

    def _load_templates_from_db(self, db: Session):
        db_templates = db.query(WorkflowTemplate).all()
        for template in db_templates:
            self.templates[template.id] = template

    def _load_templates_from_disk(self):
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory {self.templates_dir} not found")
            return

        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.templates_dir, filename), 'r') as f:
                        data = json.load(f)
                        template = WorkflowTemplate(**data)
                        self.templates[template.id] = template
                except Exception as e:
                    logger.error(f"Failed to load template {filename}: {e}")

    def get_all_templates(self) -> List[WorkflowTemplate]:
        return list(self.templates.values())

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        template = self.templates.get(template_id)
        if not template and self.db:
            template = self.db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
            if template:
                self.templates[template_id] = template
        return template

    def match_intent(self, query: str) -> List[Dict[str, Any]]:
        """
        Simple keyword-based matching (AI agent will do better)
        """
        matches = []
        query = query.lower()

        for template in self.templates.values():
            score = 0
            if any(keyword.lower() in query for keyword in template.keywords):
                score += 0.5
            if template.name.lower() in query:
                score += 0.3

            if score > 0:
                matches.append({
                    "template": template,
                    "score": score
                })

        return sorted(matches, key=lambda x: x['score'], reverse=True)

async def load_templates():
    matcher = TemplateMatcher()
    return matcher.get_all_templates()
