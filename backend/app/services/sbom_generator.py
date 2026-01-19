"""
SBOM Generator Service
Generates Software Bill of Materials for AI-generated workflows.
Enables governance and auditability for 2026.
"""
import json
from datetime import datetime
from typing import Dict, Any

class SBOMGenerator:
    """
    Generates SBOM for tracking model, prompts, and dependencies used in a workflow.
    """

    def generate(self, workflow_id: str, user_id: str, template_id: str, n8n_id: str) -> Dict[str, Any]:
        """
        Creates a structured SBOM document.
        """
        return {
            "sbom_id": f"sbom-{workflow_id}",
            "workflow_id": workflow_id,
            "user_id": user_id,
            "template_id": template_id,
            "engine": "n8n-v1.0",
            "n8n_id": n8n_id,
            "ai_metadata": {
                "model": "claude-3-5-sonnet-20240620",
                "role": "General Automation Architect",
                "region": "Africa-North-1"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "compliance": {
                "gdpr": "compliant",
                "algeria_data_protection": "compliant"
            }
        }

sbom_generator = SBOMGenerator()
