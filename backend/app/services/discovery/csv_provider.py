import csv
import io
import re

from app.services.discovery.base import BusinessDiscoveryProvider, DiscoveredBusiness

# Maps expected CSV header names (case-insensitive) to DiscoveredBusiness fields.
_COLUMN_ALIASES: dict[str, str] = {
    "name": "name",
    "business_name": "name",
    "category": "category",
    "type": "category",
    "address": "address",
    "city": "city",
    "state": "state",
    "country": "country",
    "latitude": "latitude",
    "lat": "latitude",
    "longitude": "longitude",
    "lng": "longitude",
    "lon": "longitude",
    "phone": "phone",
    "phone_number": "phone",
    "email": "email",
    "website": "website",
    "url": "website",
    "rating": "rating",
    "review_count": "review_count",
    "reviews": "review_count",
    "google_maps_url": "google_maps_url",
}

_FLOAT_FIELDS = {"latitude", "longitude", "rating"}
_INT_FIELDS = {"review_count"}


class CSVProvider(BusinessDiscoveryProvider):
    """Imports businesses from a CSV file (spec section 12: CSV import).
    Column names are matched case-insensitively against a small alias
    table; unrecognized columns are ignored. Rows without a `name` are
    skipped rather than guessed at."""

    def discover(self, csv_text: str | None = None, file_path: str | None = None, **kwargs) -> list[DiscoveredBusiness]:
        if csv_text is None:
            if file_path is None:
                raise ValueError("CSVProvider.discover requires csv_text or file_path")
            with open(file_path, encoding="utf-8-sig") as f:
                csv_text = f.read()

        reader = csv.DictReader(io.StringIO(csv_text))
        results: list[DiscoveredBusiness] = []

        for row in reader:
            mapped: dict = {}
            for raw_key, raw_value in row.items():
                if raw_key is None:
                    continue
                normalized_key = re.sub(r"[\s_]+", "_", raw_key.strip().lower())
                field = _COLUMN_ALIASES.get(normalized_key)
                if field is None or raw_value is None or raw_value.strip() == "":
                    continue
                value = raw_value.strip()
                if field in _FLOAT_FIELDS:
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                elif field in _INT_FIELDS:
                    try:
                        value = int(float(value))
                    except ValueError:
                        continue
                mapped[field] = value

            if not mapped.get("name"):
                continue

            results.append(DiscoveredBusiness(source="csv", **mapped))

        return results
