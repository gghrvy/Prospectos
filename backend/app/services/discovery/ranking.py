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
    if business.email:
        score = 6
    elif business.website:
        score = 4
    elif business.social_url:
        score = 2
    else:
        score = 0

    if business.phone:
        score += 1
    if not business.website:
        score += 1
    if business.address:
        score += 1
    return score


def rank_and_limit(results: list[DiscoveredBusiness], limit: int) -> list[DiscoveredBusiness]:
    """Sorts by lead quality (stable -- ties keep the API's original
    relative order, usually roughly distance-based) and returns the top
    `limit`. Call this AFTER collecting the full candidate set, never
    while still iterating/fetching, or there's nothing to rank against."""
    ranked = sorted(results, key=score_business, reverse=True)
    return ranked[:limit]
