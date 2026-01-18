import json
import os
from typing import List, Optional, Dict, Any
import logging
from app.models.workflow import WorkflowTemplate

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

class TemplateMatcher:
    """
    Manages workflow templates and matches user intent to templates
    """

    def __init__(self, templates_dir: Optional[str] = None, db: Optional[Session] = None):
        self.templates_dir = templates_dir or os.getenv("TEMPLATES_DIR", "templates")
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._load_templates_from_disk()
        if db:
            self._load_templates_from_db(db)

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
        return self.templates.get(template_id)

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
