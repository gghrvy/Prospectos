from app.services.discovery.base import BusinessDiscoveryProvider, DiscoveredBusiness


class ManualProvider(BusinessDiscoveryProvider):
    """Wraps a single hand-entered business (e.g. from a "New Prospect"
    form) in the same DiscoveredBusiness shape as the other providers, so
    it flows through the same dedup + create path."""

    def discover(self, **kwargs) -> list[DiscoveredBusiness]:
        business = DiscoveredBusiness(source="manual", **kwargs)
        return [business]
