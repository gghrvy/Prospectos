"""ProspectOS CLI. Run from `backend/` with the venv active:

    python -m app search --category plumber --city Austin [--save]
    python -m app audit <business_id>
    python -m app audit-all
    python -m app score-all
    python -m app generate-outreach <business_id> [--angle ANGLE]
    python -m app export <path.csv>
"""

import argparse
import csv
import sys

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.business import Business
from app.models.outreach import Outreach
from app.models.website_audit import WebsiteAudit
from app.services.audit_pipeline import run_audit
from app.services.discovery import OpenStreetMapProvider, deduplicate_businesses
from app.services.outreach.generator import generate_outreach_draft

CSV_EXPORT_FIELDS = [
    "id", "name", "category", "address", "city", "state", "country",
    "phone", "email", "website", "source", "rating", "review_count",
    "website_status", "created_at",
]


def _new_website_status(business: Business, audit_data: dict) -> str:
    if not business.website:
        return "not_found"
    return "exists" if audit_data.get("http_status") else "unreachable"


def _run_and_save_audit(db, business: Business) -> dict:
    audit_data = run_audit(business)
    audit = WebsiteAudit(business_id=business.id, **audit_data)
    db.add(audit)
    business.website_status = _new_website_status(business, audit_data)
    discovered_email = audit_data.get("discovered_email")
    if discovered_email and not business.email:
        business.email = discovered_email
    db.commit()
    return audit_data


def cmd_search(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        candidates = OpenStreetMapProvider().discover(
            category=args.category, city=args.city, country=args.country, radius_km=args.radius_km
        )
        existing = db.scalars(select(Business)).all()
        unique = deduplicate_businesses(list(existing), candidates)

        print(f"Found {len(candidates)} candidate(s), {len(unique)} new after dedup.")
        for candidate in unique:
            print(f"  - {candidate.name} ({candidate.city or 'unknown city'})")

        if args.save:
            for candidate in unique:
                db.add(Business(**candidate.model_dump()))
            db.commit()
            print(f"Saved {len(unique)} new business(es).")
    finally:
        db.close()


def cmd_audit(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        business = db.get(Business, args.business_id)
        if not business:
            print(f"Business {args.business_id} not found.", file=sys.stderr)
            sys.exit(1)

        audit_data = _run_and_save_audit(db, business)
        print(f"Audited {business.name}: overall_opportunity_score={audit_data['overall_opportunity_score']} ({audit_data['quality_category']})")
        for reason in audit_data.get("opportunity_reasons", []):
            print(f"  - {reason}")
    finally:
        db.close()


def cmd_audit_all(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        businesses = db.scalars(select(Business)).all()
        print(f"Auditing {len(businesses)} business(es)...")
        for business in businesses:
            audit_data = _run_and_save_audit(db, business)
            print(f"  - {business.name}: {audit_data['overall_opportunity_score']} ({audit_data['quality_category']})")
    finally:
        db.close()


def cmd_score_all(args: argparse.Namespace) -> None:
    # Scoring only happens as part of a fresh audit in this MVP (no cached
    # raw HTML to re-score offline), so "score-all" re-runs the full
    # audit pipeline for every business — same as "audit-all".
    cmd_audit_all(args)


def cmd_generate_outreach(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        business = db.get(Business, args.business_id)
        if not business:
            print(f"Business {args.business_id} not found.", file=sys.stderr)
            sys.exit(1)

        latest_audit = db.scalars(
            select(WebsiteAudit)
            .where(WebsiteAudit.business_id == business.id)
            .order_by(WebsiteAudit.created_at.desc())
            .limit(1)
        ).first()
        opportunity_types = (latest_audit.opportunity_types if latest_audit else None) or ["NO_WEBSITE"]
        opportunity_reasons = (latest_audit.opportunity_reasons if latest_audit else None) or [
            "Website not found from available sources."
        ]

        draft = generate_outreach_draft(
            business_name=business.name,
            category=business.category,
            opportunity_types=opportunity_types,
            opportunity_reasons=opportunity_reasons,
            angle=args.angle,
        )
        db.add(Outreach(business_id=business.id, **draft))
        db.commit()

        print(f"Subject: {draft['subject']}\n")
        print(draft["body"])
        print(f"\n(generated_by={draft['generated_by']}, angle={draft['angle']})")
    finally:
        db.close()


def cmd_export(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        businesses = db.scalars(select(Business).order_by(Business.created_at.desc())).all()
        with open(args.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_EXPORT_FIELDS)
            writer.writeheader()
            for business in businesses:
                writer.writerow({field: getattr(business, field) for field in CSV_EXPORT_FIELDS})
        print(f"Exported {len(businesses)} business(es) to {args.path}")
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app", description="ProspectOS CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Discover businesses via OpenStreetMap")
    search_parser.add_argument("--category", required=True)
    search_parser.add_argument("--city", required=True)
    search_parser.add_argument("--country", default=None)
    search_parser.add_argument("--radius-km", type=float, default=5.0, dest="radius_km")
    search_parser.add_argument("--save", action="store_true")
    search_parser.set_defaults(func=cmd_search)

    audit_parser = subparsers.add_parser("audit", help="Audit one business's website")
    audit_parser.add_argument("business_id")
    audit_parser.set_defaults(func=cmd_audit)

    audit_all_parser = subparsers.add_parser("audit-all", help="Audit every business")
    audit_all_parser.set_defaults(func=cmd_audit_all)

    score_all_parser = subparsers.add_parser("score-all", help="Re-audit and re-score every business")
    score_all_parser.set_defaults(func=cmd_score_all)

    outreach_parser = subparsers.add_parser("generate-outreach", help="Generate an outreach draft for one business")
    outreach_parser.add_argument("business_id")
    outreach_parser.add_argument("--angle", default=None)
    outreach_parser.set_defaults(func=cmd_generate_outreach)

    export_parser = subparsers.add_parser("export", help="Export all businesses to a CSV file")
    export_parser.add_argument("path")
    export_parser.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
