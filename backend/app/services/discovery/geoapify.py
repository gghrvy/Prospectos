import httpx

from app.services.discovery.base import BusinessDiscoveryProvider, DiscoveredBusiness, social_url_from_tags
from app.services.discovery.ranking import rank_and_limit
from app.services.discovery.search_cache import search_cache

PLACES_URL = "https://api.geoapify.com/v2/places"
GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"

# Always request this many raw results from Geoapify regardless of the
# caller's display `limit` -- comfortably under the API's real 500 cap
# (verified against Geoapify's docs), costs the same single API call, and
# gives rank_and_limit() enough of a pool to actually rank rather than
# just returning whatever the API's own ordering happened to put first.
_FETCH_BATCH_SIZE = 250

# Geoapify's category taxonomy is its own (loosely OSM-derived) scheme, not
# a 1:1 mirror of OSM tags -- every string below comes verbatim from their
# published Places API taxonomy (fetched and verified 2026-08-20), not
# guessed, since a wrong category string here would silently return
# zero/wrong results exactly like the OSM path is designed to avoid.
#
# NOTE: "plumber" has no Geoapify category at all (confirmed against their
# full "service.*" list) -- plumbers and similar roaming trades are rarely
# mapped as point-of-interest data in ANY directory, Geoapify included.
# Curated friendly terms -> precise category. This is deliberately broad
# (prospecting-relevant business types) but not the *only* way in --
# _resolve_category() below also does substring matching against the full
# taxonomy in _ALL_CATEGORIES, so a term missing from this dict can still
# resolve automatically instead of failing outright.
_CATEGORY_MAP: dict[str, str] = {
    # Trades / home services
    "electrician": "service.electrician",
    "locksmith": "service.locksmith",
    "carpenter": "service.carpenter",
    "blacksmith": "service.blacksmith",
    "chimney_sweeper": "service.chimney_sweeper",
    "auto_repair": "service.vehicle.repair.car",
    "car_repair": "service.vehicle.repair.car",
    "motorcycle_repair": "service.vehicle.repair.motorcycle",
    "car_wash": "service.vehicle.car_wash",
    "tailor": "service.tailor",
    "shoemaker": "service.shoemaker",
    "watchmaker": "service.watchmaker",
    "dry_cleaning": "service.cleaning.dry_cleaning",
    "laundry": "service.cleaning.laundry",
    "photographer": "service.photographer",
    "taxi": "service.taxi",
    "funeral_home": "service.funeral_directors",
    # Beauty / personal care
    "hairdresser": "service.beauty.hairdresser",
    "salon": "service.beauty.hairdresser",
    "barber": "service.beauty.hairdresser",
    "spa": "leisure.spa",
    "massage": "service.beauty.massage",
    "tattoo": "service.beauty.tattoo",
    "tanning_salon": "service.beauty.tanning_salon",
    "nail_salon": "service.beauty",
    "gym": "sport.fitness.gym",
    "fitness_centre": "sport.fitness.fitness_centre",
    "dojo": "sport.dojo",
    "yoga": "sport.fitness",
    # Professional / office
    "lawyer": "office.lawyer",
    "attorney": "office.lawyer",
    "accountant": "office.accountant",
    "tax_advisor": "office.tax_advisor",
    "notary": "office.notary",
    "real_estate": "office.estate_agent",
    "estate_agent": "office.estate_agent",
    "insurance": "office.insurance",
    "financial_advisor": "office.financial_advisor",
    "architect": "office.architect",
    "consulting": "office.consulting",
    "advertising_agency": "office.advertising_agency",
    "marketing_agency": "office.advertising_agency",
    "employment_agency": "office.employment_agency",
    "recruiter": "office.employment_agency",
    "it_company": "office.it",
    "software_company": "office.it",
    "coworking": "office.coworking",
    "travel_agent": "office.travel_agent",
    "travel_agency": "service.travel_agency",
    "logistics": "office.logistics",
    "telecommunication": "office.telecommunication",
    "security_company": "office.security",
    # Healthcare
    "dentist": "healthcare.dentist",
    "orthodontist": "healthcare.dentist.orthodontics",
    "doctor": "healthcare.clinic_or_praxis.general",
    "clinic": "healthcare.clinic_or_praxis.general",
    "hospital": "healthcare.hospital",
    "pharmacy": "healthcare.pharmacy",
    "optician": "commercial.health_and_beauty.optician",
    "chiropractor": "healthcare.clinic_or_praxis",
    "physiotherapist": "healthcare.clinic_or_praxis",
    "veterinary": "pet.veterinary",
    "vet": "pet.veterinary",
    # Food & drink
    "restaurant": "catering.restaurant",
    "cafe": "catering.cafe",
    "coffee_shop": "catering.cafe.coffee_shop",
    "bar": "catering.bar",
    "pub": "catering.pub",
    "bakery": "commercial.food_and_drink.bakery",
    "butcher": "commercial.food_and_drink.butcher",
    "deli": "commercial.food_and_drink.deli",
    "brewery": "production.brewery",
    "winery": "production.winery",
    "distillery": "production.distillery",
    "fast_food": "catering.fast_food",
    "food_truck": "catering.fast_food",
    "caterer": "catering",
    "grocery": "commercial.supermarket",
    "supermarket": "commercial.supermarket",
    "convenience_store": "commercial.convenience",
    # Retail
    "florist": "commercial.florist",
    "clothing": "commercial.clothing",
    "boutique": "commercial.clothing",
    "shoe_store": "commercial.clothing.shoes",
    "jewelry": "commercial.jewelry",
    "hardware": "commercial.houseware_and_hardware.hardware_and_tools",
    "furniture_store": "commercial.furniture_and_interior",
    "electronics_store": "commercial.elektronics",
    "bookstore": "commercial.books",
    "pet_store": "commercial.pet",
    "toy_store": "commercial.toy_and_game",
    "gift_shop": "commercial.gift_and_souvenir",
    "garden_centre": "commercial.garden",
    "second_hand": "commercial.second_hand",
    "shopping_mall": "commercial.shopping_mall",
    "stationery": "commercial.stationery",
    "bicycle_shop": "commercial.outdoor_and_sport.bicycle",
    "sporting_goods": "commercial.outdoor_and_sport",
    # Accommodation / hospitality
    "hotel": "accommodation.hotel",
    "motel": "accommodation.motel",
    "hostel": "accommodation.hostel",
    "guest_house": "accommodation.guest_house",
    # Rentals
    "car_rental": "rental.car",
    "bike_rental": "rental.bicycle",
    "boat_rental": "rental.boat",
    "storage_rental": "rental.storage",
    # Education / childcare
    "school": "education.school",
    "driving_school": "education.driving_school",
    "language_school": "education.language_school",
    "music_school": "education.music_school",
    "daycare": "childcare.kindergarten",
    "kindergarten": "childcare.kindergarten",
    # Entertainment / leisure
    "cinema": "entertainment.cinema",
    "theatre": "entertainment.culture.theatre",
    "gallery": "entertainment.culture.gallery",
    "museum": "entertainment.museum",
    "bowling_alley": "entertainment.bowling_alley",
    "arcade": "entertainment.amusement_arcade",
    # Financial services
    "bank": "service.financial.bank",
    "atm": "service.financial.atm",
    "money_transfer": "service.financial.money_transfer",
}

# Public so the API layer can offer these as known-good suggestions
# alongside OSM's own list, mirroring KNOWN_CATEGORIES in openstreetmap.py.
GEOAPIFY_KNOWN_CATEGORIES = sorted(_CATEGORY_MAP.keys())

# The full, verbatim business-relevant slice of Geoapify's published Places
# API taxonomy (fetched and verified 2026-08-20 -- see _CATEGORY_MAP's
# comment). Deliberately excludes non-business sections (roads, waterways,
# natural features, administrative boundaries, power infrastructure,
# parking, public transport, postal codes, memorials, tourism "sights"
# like monuments/churches) since those aren't prospecting targets and
# including them would make substring matching noisier and occasionally
# wrong (e.g. "office" matching "post.office").
_FULL_TAXONOMY_RAW = """
accommodation accommodation.apartment accommodation.chalet accommodation.guest_house accommodation.hostel accommodation.hotel accommodation.hut accommodation.motel
activity activity.community_center activity.events_venue activity.hackerspace activity.sport_club
commercial commercial.agrarian commercial.antiques commercial.art commercial.baby_goods commercial.bag commercial.books commercial.chemist commercial.clothing commercial.clothing.accessories commercial.clothing.clothes commercial.clothing.kids commercial.clothing.men commercial.clothing.shoes commercial.clothing.sport commercial.clothing.underwear commercial.clothing.women commercial.convenience commercial.department_store commercial.discount_store commercial.elektronics commercial.energy commercial.erotic commercial.florist commercial.food_and_drink commercial.food_and_drink.bakery commercial.food_and_drink.butcher commercial.food_and_drink.cheese_and_dairy commercial.food_and_drink.chocolate commercial.food_and_drink.coffee_and_tea commercial.food_and_drink.confectionery commercial.food_and_drink.deli commercial.food_and_drink.drinks commercial.food_and_drink.farm commercial.food_and_drink.frozen_food commercial.food_and_drink.fruit_and_vegetable commercial.food_and_drink.health_food commercial.food_and_drink.honey commercial.food_and_drink.ice_cream commercial.food_and_drink.nuts commercial.food_and_drink.organic commercial.food_and_drink.pasta commercial.food_and_drink.rice commercial.food_and_drink.seafood commercial.food_and_drink.spices commercial.furniture_and_interior commercial.furniture_and_interior.bathroom commercial.furniture_and_interior.bed commercial.furniture_and_interior.carpet commercial.furniture_and_interior.curtain commercial.furniture_and_interior.kitchen commercial.furniture_and_interior.lighting commercial.garden commercial.gas commercial.gift_and_souvenir commercial.health_and_beauty commercial.health_and_beauty.cosmetics commercial.health_and_beauty.hearing_aids commercial.health_and_beauty.herbalist commercial.health_and_beauty.medical_supply commercial.health_and_beauty.optician commercial.health_and_beauty.pharmacy commercial.health_and_beauty.wigs commercial.hobby commercial.hobby.anime commercial.hobby.art commercial.hobby.brewing commercial.hobby.collecting commercial.hobby.games commercial.hobby.model commercial.hobby.music commercial.hobby.photo commercial.hobby.sewing_and_knitting commercial.houseware_and_hardware commercial.houseware_and_hardware.building_materials commercial.houseware_and_hardware.building_materials.doors commercial.houseware_and_hardware.building_materials.flooring commercial.houseware_and_hardware.building_materials.glaziery commercial.houseware_and_hardware.building_materials.paint commercial.houseware_and_hardware.building_materials.tiles commercial.houseware_and_hardware.building_materials.windows commercial.houseware_and_hardware.doityourself commercial.houseware_and_hardware.fireplace commercial.houseware_and_hardware.hardware_and_tools commercial.houseware_and_hardware.swimming_pool commercial.jewelry commercial.kiosk commercial.marketplace commercial.newsagent commercial.outdoor_and_sport commercial.outdoor_and_sport.bicycle commercial.outdoor_and_sport.diving commercial.outdoor_and_sport.fishing commercial.outdoor_and_sport.golf commercial.outdoor_and_sport.hunting commercial.outdoor_and_sport.ski commercial.outdoor_and_sport.water_sports commercial.pet commercial.pyrotechnics commercial.second_hand commercial.shopping_mall commercial.smoking commercial.stationery commercial.supermarket commercial.tickets_and_lottery commercial.toy_and_game commercial.trade commercial.vehicle commercial.video_and_music commercial.watches commercial.weapons commercial.wedding
catering catering.bar catering.biergarten catering.cafe catering.cafe.bubble_tea catering.cafe.cake catering.cafe.coffee catering.cafe.coffee_shop catering.cafe.crepe catering.cafe.dessert catering.cafe.donut catering.cafe.frozen_yogurt catering.cafe.ice_cream catering.cafe.tea catering.cafe.waffle catering.fast_food catering.fast_food.burger catering.fast_food.fish_and_chips catering.fast_food.hot_dog catering.fast_food.kebab catering.fast_food.noodle catering.fast_food.pita catering.fast_food.pizza catering.fast_food.ramen catering.fast_food.salad catering.fast_food.sandwich catering.fast_food.soup catering.fast_food.tacos catering.fast_food.tapas catering.fast_food.wings catering.food_court catering.ice_cream catering.pub catering.restaurant catering.restaurant.afghan catering.restaurant.african catering.restaurant.american catering.restaurant.arab catering.restaurant.argentinian catering.restaurant.asian catering.restaurant.austrian catering.restaurant.balkan catering.restaurant.barbecue catering.restaurant.bavarian catering.restaurant.beef_bowl catering.restaurant.belgian catering.restaurant.bolivian catering.restaurant.brazilian catering.restaurant.burger catering.restaurant.caribbean catering.restaurant.chicken catering.restaurant.chili catering.restaurant.chinese catering.restaurant.croatian catering.restaurant.cuban catering.restaurant.curry catering.restaurant.czech catering.restaurant.danish catering.restaurant.dumpling catering.restaurant.ethiopian catering.restaurant.european catering.restaurant.filipino catering.restaurant.fish catering.restaurant.fish_and_chips catering.restaurant.french catering.restaurant.friture catering.restaurant.georgian catering.restaurant.german catering.restaurant.greek catering.restaurant.hawaiian catering.restaurant.hungarian catering.restaurant.indian catering.restaurant.indonesian catering.restaurant.international catering.restaurant.irish catering.restaurant.italian catering.restaurant.jamaican catering.restaurant.japanese catering.restaurant.kebab catering.restaurant.korean catering.restaurant.latin_american catering.restaurant.lebanese catering.restaurant.malay catering.restaurant.malaysian catering.restaurant.mediterranean catering.restaurant.mexican catering.restaurant.moroccan catering.restaurant.nepalese catering.restaurant.noodle catering.restaurant.oriental catering.restaurant.pakistani catering.restaurant.persian catering.restaurant.peruvian catering.restaurant.pita catering.restaurant.pizza catering.restaurant.portuguese catering.restaurant.ramen catering.restaurant.regional catering.restaurant.russian catering.restaurant.sandwich catering.restaurant.seafood catering.restaurant.soup catering.restaurant.spanish catering.restaurant.steak_house catering.restaurant.sushi catering.restaurant.swedish catering.restaurant.syrian catering.restaurant.tacos catering.restaurant.taiwanese catering.restaurant.tapas catering.restaurant.tex-mex catering.restaurant.thai catering.restaurant.turkish catering.restaurant.ukrainian catering.restaurant.uzbek catering.restaurant.vietnamese catering.restaurant.western catering.restaurant.wings catering.taproom
education education.college education.driving_school education.language_school education.library education.music_school education.school education.university
childcare childcare.kindergarten
entertainment entertainment.activity_park entertainment.activity_park.climbing entertainment.activity_park.trampoline entertainment.amusement_arcade entertainment.aquarium entertainment.bowling_alley entertainment.cinema entertainment.culture entertainment.culture.arts_centre entertainment.culture.gallery entertainment.culture.theatre entertainment.escape_game entertainment.flying_fox entertainment.miniature_golf entertainment.museum entertainment.planetarium entertainment.theme_park entertainment.water_park entertainment.zoo
healthcare healthcare.clinic_or_praxis healthcare.clinic_or_praxis.allergology healthcare.clinic_or_praxis.cardiology healthcare.clinic_or_praxis.dermatology healthcare.clinic_or_praxis.endocrinology healthcare.clinic_or_praxis.gastroenterology healthcare.clinic_or_praxis.general healthcare.clinic_or_praxis.gynaecology healthcare.clinic_or_praxis.occupational healthcare.clinic_or_praxis.ophthalmology healthcare.clinic_or_praxis.orthopaedics healthcare.clinic_or_praxis.otolaryngology healthcare.clinic_or_praxis.paediatrics healthcare.clinic_or_praxis.psychiatry healthcare.clinic_or_praxis.pulmonology healthcare.clinic_or_praxis.radiology healthcare.clinic_or_praxis.rheumatology healthcare.clinic_or_praxis.trauma healthcare.clinic_or_praxis.urology healthcare.clinic_or_praxis.vascular_surgery healthcare.dentist healthcare.dentist.orthodontics healthcare.hospital healthcare.pharmacy
leisure.spa leisure.spa.public_bath leisure.spa.sauna
office office.accountant office.advertising_agency office.architect office.association office.charity office.company office.consulting office.coworking office.diplomatic office.educational_institution office.employment_agency office.energy_supplier office.estate_agent office.financial office.financial_advisor office.forestry office.foundation office.government office.government.administrative office.government.agriculture office.government.cadaster office.government.customs office.government.education office.government.embassy office.government.environment office.government.forestry office.government.healthcare office.government.legislative office.government.migration office.government.ministry office.government.prosecutor office.government.public_service office.government.register_office office.government.social_security office.government.social_services office.government.tax office.government.transportation office.insurance office.it office.lawyer office.logistics office.newspaper office.non_profit office.notary office.political_party office.religion office.research office.security office.tax_advisor office.telecommunication office.travel_agent office.water_utility
pet pet.animal_boarding pet.animal_shelter pet.crematorium pet.dog_park pet.service pet.shop pet.veterinary
production production.beekeeper production.brewery production.cheese production.distillery production.factory production.pottery production.winery
rental rental.bicycle rental.boat rental.car rental.ski rental.storage
service service.ambulance_station service.advertising service.advertising.billboard service.advertising.column service.beauty service.beauty.hairdresser service.beauty.massage service.beauty.spa service.beauty.tanning_salon service.beauty.tattoo service.blacksmith service.bookmaker service.carpenter service.chimney_sweeper service.cleaning service.cleaning.dry_cleaning service.cleaning.laundry service.cleaning.lavoir service.crematorium service.crematorium.human service.crematorium.pet service.electrician service.estate_agent service.financial service.financial.atm service.financial.bank service.financial.bureau_de_change service.financial.money_lender service.financial.money_transfer service.financial.payment_terminal service.fire_station service.funeral_directors service.funeral_hall service.key_cutter service.locksmith service.metal_construction service.photographer service.post service.post.box service.post.office service.post.parcel_locker service.recycling service.recycling.bin service.recycling.centre service.recycling.container service.shoemaker service.social_facility service.social_facility.clothers service.social_facility.day_care service.social_facility.food service.social_facility.nursing_home service.social_facility.retirement_home service.social_facility.shelter service.tailor service.taxi service.travel_agency service.vehicle service.vehicle.car_wash service.vehicle.charging_station service.vehicle.fuel service.vehicle.repair service.vehicle.repair.car service.vehicle.repair.motorcycle service.watchmaker
sport sport.dive_centre sport.dojo sport.fishing sport.fitness sport.fitness.fitness_centre sport.fitness.fitness_station sport.fitness.gym sport.golf_course sport.horse_riding sport.ice_rink sport.pitch sport.shooting sport.skateboard sport.sports_centre sport.sports_hall sport.stadium sport.swimming_pool sport.track
camping camping.camp_pitch camping.camp_site camping.caravan_site camping.summer_camp
"""


def _flatten_category_map() -> list[str]:
    """All known category tokens available for substring-fallback matching:
    every value in _CATEGORY_MAP plus the full verified business-relevant
    taxonomy above, deduplicated. Falling back to the full taxonomy (not
    just the curated dict's tokens) is what actually gives "full
    capability" -- e.g. "sushi" isn't in the curated dict but resolves via
    catering.restaurant.sushi in the full list."""
    seen: set[str] = set(_FULL_TAXONOMY_RAW.split())
    for value in _CATEGORY_MAP.values():
        parts = value.split(".")
        for i in range(1, len(parts) + 1):
            seen.add(".".join(parts[:i]))
    return sorted(seen)


_KNOWN_TOKENS = _flatten_category_map()

# Top-level prefixes only -- Geoapify's `categories` filter matches a
# category AND everything nested under it, so listing these 16 top-level
# groups (not every leaf) covers the full business-relevant taxonomy above
# in one request. Used only for the no-category "sweep everything nearby"
# case in map mode.
_BROAD_SWEEP_CATEGORIES = ",".join(
    [
        "accommodation", "activity", "commercial", "catering", "education",
        "childcare", "entertainment", "healthcare", "leisure.spa", "office",
        "pet", "production", "rental", "service", "sport", "camping",
    ]
)


def _resolve_single_category(term: str) -> str:
    """Resolve one category term to a precise Geoapify category string.
    Tries, in order: exact curated match, exact match against the last
    segment of any known token (e.g. "bakery" -> ...food_and_drink.bakery),
    then substring match against any known token. Raises ValueError (never
    guesses) if nothing matches."""
    normalized = term.lower().strip().replace(" ", "_").replace("-", "_")

    if normalized in _CATEGORY_MAP:
        return _CATEGORY_MAP[normalized]

    for token in _KNOWN_TOKENS:
        if token.split(".")[-1] == normalized:
            return token

    for token in _KNOWN_TOKENS:
        if normalized in token:
            return token

    raise ValueError(
        f"Geoapify has no category matching {term!r} -- it covers most business types but not "
        "every term (notably: plumber, which no free directory maps well). Try a more common "
        "synonym, OpenStreetMap directly, or CSV import / manual add for this one."
    )


def _resolve_category(category: str | None) -> str:
    """Resolves a (possibly comma-separated) category string into a
    Geoapify `categories` filter value. Multiple terms are OR'd together in
    a single API call (e.g. "cafe, restaurant" -> one request covering
    both) rather than costing one call per category. A blank/None category
    (map mode, no filter typed) sweeps every business-relevant top-level
    category in one request instead of requiring a specific term."""
    if category is None or not category.strip():
        return _BROAD_SWEEP_CATEGORIES
    terms = [t for t in (part.strip() for part in category.split(",")) if t]
    if not terms:
        return _BROAD_SWEEP_CATEGORIES
    return ",".join(_resolve_single_category(t) for t in terms)


class GeoapifyProvider(BusinessDiscoveryProvider):
    """Free-tier (no credit card, ~3000 req/day) business search, used as an
    automatic fallback when OpenStreetMap's Overpass API is unavailable —
    genuinely independent infrastructure, not another Overpass mirror, so a
    broad Overpass outage doesn't take discovery down with it. Opt-in: only
    used when GEOAPIFY_API_KEY is configured; OSM stays the primary,
    always-tried-first source either way."""

    def __init__(self, api_key: str, http_client: httpx.Client | None = None):
        self._api_key = api_key
        self._client = http_client or httpx.Client(timeout=30.0)

    def discover(
        self,
        category: str | None = None,
        city: str | None = None,
        country: str | None = None,
        radius_km: float = 5.0,
        limit: int = 50,
        latitude: float | None = None,
        longitude: float | None = None,
        **kwargs,
    ) -> list[DiscoveredBusiness]:
        # Resolves comma-separated multi-category terms into a single OR'd
        # Geoapify `categories` filter, so "cafe, restaurant" costs one API
        # call, not two.
        geoapify_category = _resolve_category(category)

        if latitude is not None and longitude is not None:
            lat, lon = latitude, longitude
        else:
            if not city:
                raise ValueError("Either city or latitude/longitude must be provided.")
            lat, lon = self._geocode(city, country)

        # Cache key deliberately omits `limit` -- the raw fetch below always
        # pulls the same generous batch regardless of how many results the
        # caller wants displayed, so two searches of the same spot with
        # different limits (e.g. a quick look vs. "save all") share one
        # cached fetch instead of hitting the API twice.
        cache_key = search_cache.make_key(
            "geoapify", geoapify_category, city, country, lat, lon, radius_km, _FETCH_BATCH_SIZE
        )
        cached = search_cache.get(cache_key)
        if cached is not None:
            return rank_and_limit(cached, limit)

        response = self._client.get(
            PLACES_URL,
            params={
                "categories": geoapify_category,
                "filter": f"circle:{lon},{lat},{int(radius_km * 1000)}",
                # Always fetch a generous batch (one API call either way,
                # same quota cost) instead of asking Geoapify for exactly
                # `limit` results -- Geoapify's own ordering isn't ranked by
                # "how good a lead is this", so asking for only `limit`
                # meant good candidates past that cutoff were never even
                # fetched, let alone considered. Rank locally after the
                # fact instead (see rank_and_limit below).
                "limit": _FETCH_BATCH_SIZE,
                "apiKey": self._api_key,
            },
        )
        response.raise_for_status()
        features = response.json().get("features", [])

        results: list[DiscoveredBusiness] = []
        for feature in features:
            props = feature.get("properties", {})
            name = props.get("name")
            if not name:
                continue

            # address_line1 is actually the place NAME in Geoapify's
            # formatting (not a street address) -- build a real one from
            # street/housenumber instead, matching the OSM provider's style.
            street_parts = [props.get("housenumber"), props.get("street")]
            address = " ".join(str(p) for p in street_parts if p) or None

            contact = props.get("contact", {})
            # Social tags aren't in Geoapify's own `contact` object -- they
            # only show up in the raw OSM tags Geoapify passes through when
            # the place is OSM-sourced (the common case). Same helper as
            # the OSM provider uses, so a facebook/instagram tag is
            # captured here too instead of only on the OSM path.
            raw_tags = props.get("datasource", {}).get("raw", {})

            results.append(
                DiscoveredBusiness(
                    name=name,
                    category=category,
                    address=address,
                    city=props.get("city") or city,
                    state=props.get("state"),
                    country=props.get("country") or country,
                    latitude=props.get("lat"),
                    longitude=props.get("lon"),
                    phone=contact.get("phone"),
                    email=contact.get("email"),
                    website=props.get("website"),
                    social_url=social_url_from_tags(raw_tags),
                    source="geoapify",
                    source_url=self._source_url(props),
                )
            )

        search_cache.set(cache_key, results)
        return rank_and_limit(results, limit)

    @staticmethod
    def _source_url(props: dict) -> str | None:
        """Most Geoapify results are themselves sourced from OpenStreetMap
        (visible in datasource.raw.osm_type/osm_id) -- reconstruct the real,
        human-clickable OSM page when that's the case, same as the OSM
        provider's own source_url, instead of pointing at a JSON API
        endpoint no one can usefully open in a browser."""
        raw = props.get("datasource", {}).get("raw", {})
        osm_type_code = raw.get("osm_type")
        osm_id = raw.get("osm_id")
        osm_type = {"n": "node", "w": "way", "r": "relation"}.get(osm_type_code)
        if osm_type and osm_id:
            return f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
        return None

    def geocode(self, place: str) -> dict:
        """Public single-place geocode, mirroring OpenStreetMapProvider's
        interface so the API layer can fall back to this one uniformly."""
        response = self._client.get(GEOCODE_URL, params={"text": place, "limit": 1, "apiKey": self._api_key})
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            raise ValueError(f"Could not find a location matching {place!r}.")
        lon, lat = features[0]["geometry"]["coordinates"]
        return {
            "latitude": lat,
            "longitude": lon,
            "display_name": features[0].get("properties", {}).get("formatted", place),
        }

    def _geocode(self, city: str, country: str | None) -> tuple[float, float]:
        query = city if not country else f"{city}, {country}"
        result = self.geocode(query)
        return result["latitude"], result["longitude"]
