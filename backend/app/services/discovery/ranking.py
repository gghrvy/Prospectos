"""Ranks discovered candidates by how useful they are as a prospecting
lead, before the result set gets truncated to the caller's requested
`limit`.

The bug this fixes: both providers used to build results in whatever
order the underlying API/query happened to return them (Overpass's
internal element order; Geoapify's own relevance/distance ordering) and
then just take the first N. That's arbitrary with respect to what
actually matters here -- "is this a good lead for a web-dev/AI-automation
pitch" -- so a genuinely great prospect sitting at position 51 in that
arbitrary order was silently dropped in favor of a mediocre one at
position 12. Ranking by lead quality before slicing means the businesses
that get through the cutoff are the ones actually worth reaching out to.
"""

from app.services.discovery.base import DiscoveredBusiness


def score_business(business: DiscoveredBusiness) -> int:
    """Higher = better lead. Reachability dominates the score, not "needs
    a website" -- outreach here only has two paths in: an email already
    present in the discovery data, or one extracted by crawling the
    business's own site during an audit. A business with no website AND
    no listed email has no automated path to contact at all, so it must
    not outrank one we can actually email, no matter how good a sales
    opportunity it looks like on paper.

    Reachability tier (dominant):
      - Has an email already            -> ready to draft/send right now
      - Has a website, no email yet     -> reachable once audited (the
                                            crawler often finds a contact
                                            email or at least confirms a
                                            contact form)
      - Neither                          -> no automated path in; scores 0
                                            on this dimension deliberately

    Secondary tiebreakers (small, only separate leads within the same
    reachability tier):
      - No website: still the actual sales opportunity this app is built
        around, so it nudges otherwise-equal leads up -- just not enough
        to beat genuine reachability.
      - Has a phone: an extra contact channel (not automated yet, but a
        human could still call).
      - Has an address: more likely a real, currently-operating listing
        rather than a stale/incomplete map entry.

    A no-website business with a Facebook/Instagram page (`social_url`)
    is meaningfully more reachable than one with nothing at all -- a
    human can still send a direct message -- so it sits between the
    "has website" and "has nothing" tiers rather than at the bottom.
    """
    score = 0
    if business.email: score += 35
    elif business.website: score += 22
    elif business.social_url: score += 10
    if business.website: score += 12
    else: score += 18
    if business.phone: score += 10
    if business.address: score += 10
    if business.review_count and business.review_count >= 25: score += 10
    if business.rating and business.rating >= 4: score += 5
    return min(100, score)


def rank_and_limit(results: list[DiscoveredBusiness], limit: int) -> list[DiscoveredBusiness]:
    """Sorts by lead quality (stable -- ties keep the API's original
    relative order, usually roughly distance-based) and returns the top
    `limit`. Call this AFTER collecting the full candidate set, never
    while still iterating/fetching, or there's nothing to rank against."""
    for business in results:
        score = score_business(business)
        reasons = []
        if business.email: reasons.append("email ready")
        elif business.website: reasons.append("website to audit")
        if business.review_count and business.review_count >= 25: reasons.append(f"{business.review_count} reviews")
        if not business.website: reasons.append("no website")
        business.prospect_fit_score = score
        business.prospect_fit_reason = ", ".join(reasons) or "limited contact data"
    ranked = sorted(results, key=lambda item: item.prospect_fit_score or 0, reverse=True)
    return ranked[:limit]
