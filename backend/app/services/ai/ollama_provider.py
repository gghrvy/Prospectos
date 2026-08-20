import httpx

from app.services.ai.base import AIProvider

OLLAMA_PROBE_TIMEOUT_SECONDS = 2.0
OLLAMA_GENERATE_TIMEOUT_SECONDS = 60.0


class OllamaProvider(AIProvider):
    """Generates outreach copy using a locally running Ollama model. Fully
    optional (spec section 25-26) — `is_available()` does a fast probe so
    callers can fall back to TemplateProvider when Ollama isn't running."""

    def __init__(self, base_url: str, model: str, http_client: httpx.Client | None = None):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = http_client or httpx.Client()

    def is_available(self) -> bool:
        try:
            response = self._client.get(f"{self._base_url}/api/tags", timeout=OLLAMA_PROBE_TIMEOUT_SECONDS)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def generate_outreach(
        self,
        business_name: str,
        category: str | None,
        angle: str,
        observations: list[str],
        sender: dict | None = None,
        social_proof: dict | None = None,
    ) -> tuple[str, str]:
        prompt = self._build_prompt(business_name, category, angle, observations, social_proof)
        raw = self._call_ollama(prompt)
        return self._parse_subject_and_body(raw, business_name)

    def _build_prompt(
        self,
        business_name: str,
        category: str | None,
        angle: str,
        observations: list[str],
        social_proof: dict | None = None,
    ) -> str:
        observations_text = "\n".join(f"- {o}" for o in observations) or "- (no specific observations)"
        rating = (social_proof or {}).get("rating")
        review_count = (social_proof or {}).get("review_count")
        if rating and review_count and rating >= 4.0 and review_count >= 3:
            proof_instruction = (
                f"This business has a real, verified {rating:g}-star rating from {review_count} reviews. You MAY "
                "use this once as a liking/authority cue (e.g. 'with a X-star rating, people clearly like what you "
                "do') -- but only this exact number, never a rounder or more flattering one.\n"
            )
        else:
            proof_instruction = (
                "No verified rating data is available for this business -- do not mention ratings, reviews, or "
                "'other customers' at all; that would be fabricated social proof.\n"
            )
        return (
            "You are writing a short, respectful cold outreach email from a small web development and AI "
            f'automation studio to a local business called "{business_name}" ({category or "local business"}).\n'
            "Use ONLY these verified observations about their website — never invent facts, never insult them:\n"
            f"{observations_text}\n\n"
            f"The angle to pitch is: {angle}.\n"
            f"{proof_instruction}"
            "Structure and copywriting guidance (honest persuasion only — no fake urgency/scarcity, no invented "
            "social proof, nothing beyond what these observations actually support):\n"
            "1) Subject line: specific and curiosity-driven (e.g. 'Something I noticed on their site'), never a "
            "generic template phrase like 'Quick idea for X'.\n"
            "2) Observation: the specific, factual finding above.\n"
            "3) Consequence, loss-framed: what a real visitor misses out on right now because of THIS SPECIFIC "
            "finding — not a generic line about after-hours visitors unless the finding is actually about "
            "after-hours contact. Tie the consequence to the observation you just stated, concretely (a visitor "
            "who leaves, a call that never happens) rather than an abstract 'missed opportunity'.\n"
            "4) Benefit: the fix, tied to the angle.\n"
            "5) Call-to-action: offer something small and concrete for free (e.g. a quick mockup), and make the "
            "ask itself trivial — 'just reply' beats an open-ended 'let me know'.\n"
            "Do NOT invent a sender name, company name, or sign-off (no 'Best,', no name) — the email body should "
            "end right after the call-to-action; a real signature is appended separately afterward.\n"
            "Keep it under 120 words, friendly and professional, no exclamation marks, no generic flattery. Open "
            "with 'Hi there,' (never 'Hi [Business Name],' — that reads like addressing a company as a person) "
            "and put the business name naturally in the first sentence instead, e.g. 'I took a look at "
            f'{business_name}\'s site and noticed...\'\n'
            "Respond with exactly: a first line 'Subject: ...', a blank line, then the email body."
        )

    def _call_ollama(self, prompt: str) -> str:
        response = self._client.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=OLLAMA_GENERATE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    @staticmethod
    def _parse_subject_and_body(raw: str, business_name: str) -> tuple[str, str]:
        lines = raw.splitlines()
        subject = f"Quick idea for {business_name}"
        body = raw
        for i, line in enumerate(lines):
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
                body = "\n".join(lines[i + 1 :]).strip()
                break
        return subject, body
