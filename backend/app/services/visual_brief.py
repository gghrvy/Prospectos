from app.models.business import Business
from app.models.website_audit import WebsiteAudit


def generate_visual_brief(business: Business, audit: WebsiteAudit) -> str:
    assessments = audit.opportunity_assessments or []
    primary = next((item for item in assessments if item.get("classification") == "PRIMARY"), None)
    if not primary:
        raise ValueError("No sufficiently strong, evidence-backed opportunity is available for a visual brief.")
    secondary = [item for item in assessments if item.get("classification") == "SECONDARY"]
    quality = ", ".join(
        f"{label} {getattr(audit, field)}/100" for label, field in (
            ("mobile", "mobile_score"), ("design", "design_score"), ("technical", "technical_score"), ("conversion", "conversion_score")
        ) if getattr(audit, field) is not None
    )
    preserve = "Preserve the existing website and branding; layer the primary improvement naturally into the current experience."
    if primary["opportunity_type"] in {"WEBSITE_REDESIGN", "NO_WEBSITE"}:
        preserve = "Propose a focused new visual direction centered on the primary customer action."
    lines = [
        "PROSPECT VISUAL BRIEF", "", f"Company: {business.name}", f"Website: {business.website or 'No website available'}",
        f"Business type: {business.category or 'Not specified'}", f"Existing website assessment: {quality or 'No complete website assessment available.'}", "",
        f"PRIMARY OPPORTUNITY: {primary['opportunity_type'].replace('_', ' ').title()}",
        f"Opportunity score: {primary['recommendation_score']}/100", f"Evidence: {primary['evidence']}",
        f"Why this matters: {primary['possible_impact']}", f"RECOMMENDED CONCEPT: {primary['recommended_concept']}",
        f"PRIMARY VISUAL: A polished, on-brand demonstration of {primary['recommended_concept'].lower()}",
        f"CUSTOMER FLOW: {primary['customer_flow']}", "", "SECONDARY OPPORTUNITIES:",
    ]
    if secondary:
        for item in secondary:
            lines += [f"- {item['opportunity_type'].replace('_', ' ').title()} ({item['recommendation_score']}/100)",
                      f"  Evidence: {item['evidence']}", f"  Relevance: {item['reasoning']}",
                      f"  Suggested visual concept: {item['recommended_concept']}"]
    else:
        lines.append("- None currently recommended as visual additions.")
    lines += ["", "DO NOT INCLUDE: Rejected opportunities or unsupported performance claims.", "",
              "EXISTING DESIGN GUIDANCE:", preserve, "", "AVAILABLE REFERENCES:",
              "- desktop screenshot" if audit.screenshot_desktop_path else "- desktop screenshot not available",
              "- mobile screenshot" if audit.screenshot_mobile_path else "- mobile screenshot not available",
              f"- website URL: {business.website or 'not available'}", "", "VISUAL GOAL:",
              "Create a polished one-page concept presentation customized to this business. Give the primary opportunity most visual emphasis and show secondary opportunities only as optional additions."]
    return "\n".join(lines)
