from app.models.enums import OpportunityType, PackageType


def recommend_package(opportunity_types: list[str], overall_opportunity_score: int) -> str:
    """Package recommendation rules (spec section 24):
    - CUSTOM when the findings specifically call for custom AI automation.
    - FULL when there's no website at all, the findings add up to a full
      digital upgrade, or the overall opportunity score is high.
    - STANDARD otherwise — still worth reaching out, smaller scope.
    """
    if OpportunityType.CUSTOM_AI_AUTOMATION.value in opportunity_types:
        return PackageType.CUSTOM.value

    if (
        OpportunityType.NO_WEBSITE.value in opportunity_types
        or OpportunityType.FULL_DIGITAL_UPGRADE.value in opportunity_types
        or overall_opportunity_score >= 70
    ):
        return PackageType.FULL.value

    return PackageType.STANDARD.value
