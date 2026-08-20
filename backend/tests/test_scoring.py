from app.services.analyzer.analyzer import analyze_crawl, quality_category_for_score
from app.services.scoring.package_recommendation import recommend_package
from app.services.scoring.scoring import score_no_website, score_website
from tests.test_analyzer import _bad_crawl_result, _good_crawl_result


def test_score_no_website_is_maximal_opportunity():
    result = score_no_website()

    assert result.overall_opportunity_score >= 90
    assert "NO_WEBSITE" in result.opportunity_types
    assert result.opportunity_reasons  # never a bare score with no explanation
    assert "Website not found from available sources." in result.opportunity_reasons


def test_bad_site_scores_higher_opportunity_than_good_site():
    """The core required scenario: a bad site should score as a HIGH
    opportunity, a good site should score LOWER."""
    good_findings = analyze_crawl(_good_crawl_result())
    good_category = quality_category_for_score(good_findings.website_quality_score)
    good_result = score_website(good_findings, good_category)

    bad_findings = analyze_crawl(_bad_crawl_result())
    bad_category = quality_category_for_score(bad_findings.website_quality_score)
    bad_result = score_website(bad_findings, bad_category)

    assert bad_result.overall_opportunity_score > good_result.overall_opportunity_score
    assert len(bad_result.opportunity_types) > len(good_result.opportunity_types)
    # Every opportunity type must carry a matching human-readable reason.
    assert len(bad_result.opportunity_types) == len(bad_result.opportunity_reasons)
    assert len(good_result.opportunity_types) == len(good_result.opportunity_reasons)


def test_good_site_still_flags_real_gaps_only():
    good_findings = analyze_crawl(_good_crawl_result())
    good_category = quality_category_for_score(good_findings.website_quality_score)
    result = score_website(good_findings, good_category)

    # The good fixture has no analytics-free gap since it includes gtag —
    # WEBSITE_REDESIGN should not fire for a high-quality site.
    assert "WEBSITE_REDESIGN" not in result.opportunity_types


def test_recommend_package_no_website_is_full():
    assert recommend_package(["NO_WEBSITE", "FULL_DIGITAL_UPGRADE"], overall_opportunity_score=95) == "FULL"


def test_recommend_package_custom_ai_automation_wins():
    assert recommend_package(["AI_CHATBOT", "CUSTOM_AI_AUTOMATION"], overall_opportunity_score=50) == "CUSTOM"


def test_recommend_package_low_opportunity_is_standard():
    assert recommend_package(["MOBILE_IMPROVEMENT"], overall_opportunity_score=20) == "STANDARD"
