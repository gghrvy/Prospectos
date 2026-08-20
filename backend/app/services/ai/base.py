from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstraction over "how do we turn audit findings into an outreach
    draft" (spec section 26). OllamaProvider uses a local LLM if one is
    running; TemplateProvider is a deterministic rule-based fallback that
    always works with zero AI installed. Neither calls a paid AI API."""

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_outreach(
        self,
        business_name: str,
        category: str | None,
        angle: str,
        observations: list[str],
        sender: dict | None = None,
        social_proof: dict | None = None,
    ) -> tuple[str, str]:
        """Returns (subject, body). `sender`, if given, is a dict with
        optional name/title/email/phone/portfolio_url -- implementations
        should NOT append their own sign-off; generate_outreach_draft()
        appends one consistent signature block after the provider returns,
        so every draft (template or AI) ends with the same, correct
        identity regardless of which provider wrote it.

        `social_proof`, if given, is a dict with optional rating (float)
        and review_count (int) -- real, verified numbers from the
        discovery source (Google/OSM), never fabricated. Implementations
        MAY use this for a one-line liking/authority cue ("with a 4.8
        rating, people clearly like what you do") when the numbers are
        strong enough to be worth citing, and MUST stay silent about
        ratings entirely when it's None or too thin to be meaningful --
        never invent or imply a rating that wasn't actually passed in."""
        raise NotImplementedError
