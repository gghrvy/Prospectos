from app.services.discovery.base import DiscoveredBusiness
from app.services.discovery.ranking import rank_and_limit, score_business


def _biz(**overrides) -> DiscoveredBusiness:
    defaults = dict(name="Test Co", source="openstreetmap")
    defaults.update(overrides)
    return DiscoveredBusiness(**defaults)


def test_score_prioritizes_reachability_over_bare_no_website_listing():
    # A no-website business with zero contact info has no automated path
    # to reach at all -- it must not outrank a business we can actually
    # email, even though "no website" is the better sales pitch on paper.
    unreachable_no_site = _biz(name="Unreachable")
    reachable_with_site = _biz(name="Reachable", website="https://example.com")
    assert score_business(reachable_with_site) > score_business(unreachable_no_site)


def test_score_prioritizes_has_email_over_has_website_only():
    has_email = _biz(name="Has Email", email="hi@example.com")
    has_site_only = _biz(name="Has Site", website="https://example.com")
    assert score_business(has_email) > score_business(has_site_only)


def test_score_no_website_still_breaks_ties_among_reachable_leads():
    # Among two leads we can equally reach (both have email), the one
    # that also needs a website is still the stronger sales opportunity.
    reachable_no_site = _biz(name="Reachable No Site", email="hi@example.com")
    reachable_has_site = _biz(name="Reachable Has Site", email="hi@example.com", website="https://example.com")
    assert score_business(reachable_no_site) > score_business(reachable_has_site)


def test_score_rewards_contact_info_and_address():
    bare = _biz(name="Bare", website="https://example.com")
    with_phone = _biz(name="With Phone", website="https://example.com", phone="555-1234")
    full = _biz(name="Full", website="https://example.com", phone="555-1234", address="100 Main St")
    assert score_business(bare) < score_business(with_phone) < score_business(full)


def test_rank_and_limit_keeps_the_best_leads_not_just_the_first_n():
    # Simulates the real bug: a great, reachable lead sitting near the end
    # of the raw API order used to get truncated away in favor of
    # unreachable listings that just happened to come first.
    unreachable_leads = [_biz(name=f"No Contact Info {i}") for i in range(10)]
    great_lead = _biz(name="Reachable And Needs A Site", email="hi@example.com", phone="555-9999", address="1 Main St")
    raw_order = unreachable_leads + [great_lead]  # great lead is LAST in raw order

    top_5 = rank_and_limit(raw_order, limit=5)

    assert great_lead in top_5  # would have been dropped by naive "take first 5"
    assert top_5[0] is great_lead  # ranked first: reachable + phone + address + no website


def test_rank_and_limit_is_stable_for_equal_scores():
    a = _biz(name="A", website="https://a.com")
    b = _biz(name="B", website="https://b.com")
    c = _biz(name="C", website="https://c.com")
    # All equal score (all have websites, none have phone/address) --
    # original relative order should be preserved.
    result = rank_and_limit([a, b, c], limit=3)
    assert [r.name for r in result] == ["A", "B", "C"]


def test_score_social_url_beats_nothing_but_loses_to_website_or_email():
    nothing = _biz(name="Nothing")
    social_only = _biz(name="Social Only", social_url="https://www.facebook.com/example")
    has_site = _biz(name="Has Site", website="https://example.com")
    assert score_business(nothing) < score_business(social_only) < score_business(has_site)


def test_rank_and_limit_truncates_to_requested_limit():
    many = [_biz(name=f"Co {i}") for i in range(20)]
    assert len(rank_and_limit(many, limit=5)) == 5
