from pydantic import BaseModel


class ScoringWeights(BaseModel):
    """Configurable weights for the opportunity formula (spec section 22).
    redesign/ai/conversion weights should sum to ~1.0 for
    overall_opportunity_score to land in 0-100."""

    redesign_weight: float = 0.40
    ai_gap_weight: float = 0.35
    conversion_gap_weight: float = 0.25

    no_website_overall_score: int = 95
    no_website_ai_score: int = 90
    no_website_redesign_score: int = 100


DEFAULT_WEIGHTS = ScoringWeights()
