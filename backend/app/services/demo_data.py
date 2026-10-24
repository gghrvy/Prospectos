"""Prepared, fictional records used by the public ProspectOS demo.

These objects deliberately live outside SQLAlchemy: demo requests must not
read a connected production database or create persistent records.  The
shape mirrors the API response schemas so the real UI renders its normal
scorecards, evidence, recommendations, and outreach views.
"""

from copy import deepcopy
from datetime import datetime, timezone


DEMO_TIMESTAMP = datetime(2026, 9, 15, 14, 30, tzinfo=timezone.utc)


def _assessment(kind: str, evidence: str, impact: str, concept: str, score: int, primary: bool = True) -> dict:
    return {
        "opportunity_type": kind,
        "evidence": evidence,
        "business_interpretation": impact,
        "outreach_observation": impact,
        "evidence_confidence": 92,
        "business_relevance": 88,
        "estimated_business_impact": score,
        "outreach_suitability": 86,
        "visual_demo_score": score,
        "recommendation_score": score,
        "reasoning": "Prepared fictional demonstration finding.",
        "possible_impact": impact,
        "recommended_concept": concept,
        "customer_flow": "Visitor arrives, understands the offer, and completes the primary next step.",
        "classification": "PRIMARY" if primary else "SECONDARY",
    }


def _audit(business_id: str, **values: object) -> dict:
    base = {
        "id": f"audit-{business_id}", "business_id": business_id, "url": None,
        "http_status": 200, "https_enabled": True, "title": None, "meta_description": None,
        "page_count": 4, "crawl_depth": 1, "has_viewport": True, "has_contact_form": False,
        "has_email": False, "has_phone": True, "has_booking": False, "has_faq": False,
        "has_live_chat": False, "has_ai_chatbot": False, "has_whatsapp": False,
        "has_social_links": True, "discovered_email": None, "broken_link_count": 0,
        "mobile_score": 55, "design_score": 55, "technical_score": 60, "content_score": 55,
        "conversion_score": 45, "customer_experience_score": 45, "website_quality_score": 53,
        "ai_opportunity_score": 72, "redesign_opportunity_score": 65, "overall_opportunity_score": 70,
        "quality_category": "AVERAGE", "opportunity_types": [], "opportunity_reasons": [],
        "opportunity_assessments": [], "website_context": {"source": "prepared demo data"},
        "screenshot_desktop_path": None, "screenshot_mobile_path": None, "created_at": DEMO_TIMESTAMP,
    }
    base.update(values)
    return base


def _business(identifier: str, name: str, category: str, city: str, **values: object) -> dict:
    base = {
        "id": identifier, "name": name, "category": category, "address": None, "city": city,
        "state": "CA", "country": "USA", "latitude": None, "longitude": None, "phone": None,
        "email": None, "website": None, "social_url": None, "source": "prepared_demo",
        "source_url": None, "google_maps_url": None, "rating": None, "review_count": None,
        "website_status": "exists", "created_at": DEMO_TIMESTAMP, "updated_at": DEMO_TIMESTAMP,
    }
    base.update(values)
    return base


_DENTAL_ID = "demo-brightsmile-dental"
_RESTAURANT_ID = "demo-copper-table"
_REALTY_ID = "demo-harborstone-realty"
_HOME_ID = "demo-sunrise-home-services"

_AUDITS = {
    _DENTAL_ID: _audit(
        _DENTAL_ID, url="https://brightsmile.example", title="BrightSmile Family Dental",
        meta_description="Gentle family dentistry in Redwood Heights.", page_count=6, crawl_depth=2,
        has_contact_form=True, has_email=True, has_phone=True, has_booking=False, has_faq=False,
        mobile_score=42, design_score=48, technical_score=62, content_score=58, conversion_score=34,
        customer_experience_score=38, website_quality_score=47, ai_opportunity_score=84,
        redesign_opportunity_score=76, overall_opportunity_score=86, quality_category="WEAK",
        opportunity_types=["BOOKING_AUTOMATION", "MOBILE_IMPROVEMENT", "AI_CHATBOT"],
        opportunity_reasons=["No online appointment path was found.", "The prepared mobile review shows a dense primary contact journey.", "No after-hours answer path was detected for common patient questions."],
        opportunity_assessments=[
            _assessment("BOOKING_AUTOMATION", "No booking flow on the prepared sample site.", "Patients who are ready to book have to call during office hours, creating avoidable drop-off.", "A mobile-first appointment request flow with service and insurance prompts.", 94),
            _assessment("MOBILE_IMPROVEMENT", "Prepared mobile score: 42/100.", "A simpler mobile path can make it easier for new patients to take the next step.", "A streamlined mobile service and contact layout.", 82, False),
        ],
        audit_summary="Prepared demo audit: the clinic has clear service information, but its mobile booking journey leaves a strong conversion opportunity.",
    ),
    _RESTAURANT_ID: _audit(
        _RESTAURANT_ID, url="https://coppertable.example", title="The Copper Table",
        meta_description="Seasonal neighborhood cooking and private dining.", page_count=3, crawl_depth=1,
        has_viewport=True, has_contact_form=False, has_email=False, has_phone=True, has_booking=True,
        has_faq=False, has_live_chat=False, has_ai_chatbot=False, mobile_score=79, design_score=76,
        technical_score=74, content_score=68, conversion_score=61, customer_experience_score=63,
        website_quality_score=70, ai_opportunity_score=46, redesign_opportunity_score=35,
        overall_opportunity_score=48, quality_category="GOOD", opportunity_types=["FAQ_AUTOMATION", "ANALYTICS"],
        opportunity_reasons=["Private-dining and allergy questions do not have a self-service answer path.", "No prepared evidence of conversion measurement was available."],
        opportunity_assessments=[
            _assessment("FAQ_AUTOMATION", "No FAQ or guided private-event inquiry path in the prepared sample.", "Staff can spend less time repeating common event and dietary questions.", "A private-dining concierge with menus, capacity, and allergy answers.", 58),
            _assessment("ANALYTICS", "No prepared conversion measurement signal.", "The team cannot easily see which channels create reservations and event inquiries.", "A lightweight reservation and inquiry measurement plan.", 49, False),
        ],
        audit_summary="Prepared demo audit: a polished restaurant site with targeted opportunities in private-event self-service and measurement rather than a full rebuild.",
    ),
    _REALTY_ID: _audit(
        _REALTY_ID, url="https://harborstone-realty.example", title="Harborstone Realty",
        meta_description="Boutique residential real estate in Harbor City.", page_count=8, crawl_depth=2,
        has_viewport=True, has_contact_form=True, has_email=True, has_phone=True, has_booking=False,
        has_faq=False, has_live_chat=False, has_ai_chatbot=False, mobile_score=58, design_score=63,
        technical_score=57, content_score=49, conversion_score=41, customer_experience_score=44,
        website_quality_score=52, ai_opportunity_score=88, redesign_opportunity_score=63,
        overall_opportunity_score=78, quality_category="AVERAGE", opportunity_types=["LEAD_CAPTURE", "AI_CHATBOT", "CONVERSION_IMPROVEMENT"],
        opportunity_reasons=["The prepared sample has one generic contact form for buyer and seller journeys.", "No instant answer path was detected for listing and neighborhood questions.", "Primary calls to action do not distinguish the visitor's intent."],
        opportunity_assessments=[
            _assessment("LEAD_CAPTURE", "One generic inquiry form in the prepared demo.", "Buyer and seller leads can be qualified earlier and routed to the right follow-up.", "Separate buyer, seller, and valuation request flows.", 90),
            _assessment("AI_CHATBOT", "No guided listing or neighborhood assistant in the prepared demo.", "Visitors can get answers while interest is high, before they leave the site.", "A guarded listing and neighborhood Q&A assistant.", 85, False),
        ],
        audit_summary="Prepared demo audit: the agency has a usable foundation, with meaningful upside in intent-specific lead capture and guided property questions.",
    ),
    _HOME_ID: _audit(
        _HOME_ID, url=None, http_status=None, https_enabled=None, title=None, meta_description=None,
        page_count=0, crawl_depth=0, has_viewport=None, has_contact_form=None, has_email=None,
        has_phone=None, has_booking=None, has_faq=None, has_live_chat=None, has_ai_chatbot=None,
        has_whatsapp=None, has_social_links=True, mobile_score=None, design_score=None,
        technical_score=None, content_score=None, conversion_score=None, customer_experience_score=None,
        website_quality_score=None, ai_opportunity_score=92, redesign_opportunity_score=100,
        overall_opportunity_score=95, quality_category="CRITICAL", opportunity_types=["NO_WEBSITE", "FULL_DIGITAL_UPGRADE"],
        opportunity_reasons=["No website is present in the prepared sample.", "Customers have no reliable search-to-service conversion path."],
        opportunity_assessments=[
            _assessment("NO_WEBSITE", "No website in the prepared fictional record.", "Potential customers cannot compare services, build trust, or request help online.", "A fast local-services site with urgent-request and estimate flows.", 98),
        ],
        audit_summary="Prepared demo audit: no website is available, making a focused first web presence the clearest opportunity.",
    ),
}

_BUSINESSES = [
    _business(_DENTAL_ID, "BrightSmile Family Dental", "Dental clinic", "Redwood Heights", address="120 Juniper Lane", phone="(555) 010-2401", email="hello@brightsmile.example", website="https://brightsmile.example", rating=4.7, review_count=128),
    _business(_RESTAURANT_ID, "The Copper Table", "Restaurant", "Redwood Heights", address="48 Market Row", phone="(555) 010-2402", email="events@coppertable.example", website="https://coppertable.example", rating=4.5, review_count=286),
    _business(_REALTY_ID, "Harborstone Realty", "Real estate agency", "Harbor City", address="8 Marina Avenue", phone="(555) 010-2403", email="team@harborstone-realty.example", website="https://harborstone-realty.example", rating=4.6, review_count=74),
    _business(_HOME_ID, "Sunrise Home Services", "Home services", "Cedar Grove", address="77 Beacon Road", phone="(555) 010-2404", social_url="https://social.example/sunrise-home-services", rating=4.3, review_count=42, website_status="not_found"),
]


def _draft(business_id: str, subject: str, body: str, angle: str) -> dict:
    return {"id": f"draft-{business_id}", "business_id": business_id, "angle": angle, "subject": subject, "body": body,
            "generated_by": "prepared-demo", "sender_id": None, "sender_name": "ProspectOS Demo", "sender_title": "Sample outreach", "sender_email": None,
            "sender_phone": None, "sender_portfolio_url": None, "created_at": DEMO_TIMESTAMP, "sent_at": None, "sent_to": None, "approval_status": "DRAFT", "batch_id": None}


_DRAFTS = {
    _DENTAL_ID: _draft(_DENTAL_ID, "A simpler way for new patients to book", "Hi BrightSmile team,\n\nI noticed the prepared demo of your patient journey makes it hard for a mobile visitor to request an appointment without calling. A focused booking path could help new patients take that step sooner.\n\nThis is a fictional preview only—no message will be sent.\n\nBest,\nProspectOS Demo", "BOOKING"),
    _RESTAURANT_ID: _draft(_RESTAURANT_ID, "A smoother private-dining inquiry path", "Hi Copper Table team,\n\nThe prepared example suggests guests may need to contact the team for repeated private-dining and dietary questions. A guided inquiry flow could make planning easier for both guests and staff.\n\nThis is a fictional preview only—no message will be sent.\n\nBest,\nProspectOS Demo", "FAQ_AUTOMATION"),
    _REALTY_ID: _draft(_REALTY_ID, "Helping buyers and sellers self-identify sooner", "Hi Harborstone team,\n\nThe prepared demo shows one broad contact path for very different buyer and seller needs. Intent-specific entry points could make follow-up more useful from the first inquiry.\n\nThis is a fictional preview only—no message will be sent.\n\nBest,\nProspectOS Demo", "LEAD_CAPTURE"),
    _HOME_ID: _draft(_HOME_ID, "A clear first online path for service requests", "Hi Sunrise Home Services team,\n\nThe prepared fictional record has no website, so customers have no dependable place to understand services or request help. A concise local-services site could create a strong first conversion path.\n\nThis is a fictional preview only—no message will be sent.\n\nBest,\nProspectOS Demo", "NEW_WEBSITE"),
}


def list_businesses(*, search: str | None = None, city: str | None = None, category: str | None = None, website_status: str | None = None, sort_by: str = "created_at", sort_dir: str = "desc", limit: int = 50, offset: int = 0) -> dict:
    rows = deepcopy(_BUSINESSES)
    for key, value in (("city", city), ("category", category), ("website_status", website_status)):
        if value:
            rows = [row for row in rows if str(row.get(key) or "").lower() == value.lower()]
    if search:
        needle = search.lower()
        rows = [row for row in rows if needle in " ".join(str(row.get(field) or "") for field in ("name", "city", "category")).lower()]
    rows.sort(key=lambda row: (row.get(sort_by) is None, row.get(sort_by) or ""), reverse=sort_dir == "desc")
    for row in rows:
        audit = _AUDITS[row["id"]]
        row.update({"latest_opportunity_score": audit["overall_opportunity_score"], "latest_quality_category": audit["quality_category"], "current_status": "AUDITED"})
    return {"items": rows[offset:offset + limit], "total": len(rows), "limit": limit, "offset": offset}


def business_detail(business_id: str) -> dict | None:
    business = next((deepcopy(row) for row in _BUSINESSES if row["id"] == business_id), None)
    if not business:
        return None
    audit = deepcopy(_AUDITS[business_id])
    return {**business, "current_status": "AUDITED", "latest_audit": audit, "audits": [audit], "outreach_drafts": [deepcopy(_DRAFTS[business_id])], "contracts": [], "status_history": [], "notes": []}


def audit_for(business_id: str) -> dict | None:
    audit = _AUDITS.get(business_id)
    return deepcopy(audit) if audit else None


def is_demo_business(business_id: str) -> bool:
    return business_id in _AUDITS
