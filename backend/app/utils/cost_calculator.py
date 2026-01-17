from app.config import settings

def calculate_token_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the raw cost of AI tokens in DZD
    """
    input_cost = (input_tokens / 1_000_000) * settings.CLAUDE_INPUT_COST_PER_M
    output_cost = (output_tokens / 1_000_000) * settings.CLAUDE_OUTPUT_COST_PER_M

    total_usd = input_cost + output_cost
    return total_usd * settings.DZD_TO_USD

def apply_markup(amount: float) -> float:
    """
    Applies business markup to a cost
    """
    return amount * (1 + (settings.COST_MARKUP_PERCENTAGE / 100))
