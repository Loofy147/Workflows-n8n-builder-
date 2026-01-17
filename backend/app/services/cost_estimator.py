from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CostEstimator:
    """
    Calculates estimated costs for AI tokens and workflow executions in DZD
    """

    def __init__(self):
        self.dzd_to_usd = settings.DZD_TO_USD
        self.markup = settings.COST_MARKUP_PERCENTAGE / 100.0

    def estimate_ai_cost(self, input_tokens: int, output_tokens: int, model: str = "claude-sonnet-4") -> float:
        """
        Estimate cost of AI tokens in DZD
        """
        # Costs per 1M tokens
        input_cost_usd = (input_tokens / 1_000_000) * settings.CLAUDE_INPUT_COST_PER_M
        output_cost_usd = (output_tokens / 1_000_000) * settings.CLAUDE_OUTPUT_COST_PER_M

        total_usd = input_cost_usd + output_cost_usd
        total_dzd = total_usd * self.dzd_to_usd

        # Apply markup
        final_dzd = total_dzd * (1 + self.markup)

        return round(final_dzd, 2)

    def estimate_workflow_cost(self, avg_execution_time: int, node_count: int) -> float:
        """
        Estimate cost of workflow execution in DZD
        Base price + time component + node complexity
        """
        base_price = 2.0  # 2 DZD base
        time_price = (avg_execution_time / 60.0) * 1.5  # 1.5 DZD per minute
        complexity_price = node_count * 0.5  # 0.5 DZD per node

        total_dzd = base_price + time_price + complexity_price

        return round(total_dzd, 2)
