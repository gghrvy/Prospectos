import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.cli as cli
from app import models  # noqa: F401  registers all model classes on Base
from app.database.base import Base
from app.models.business import Business
from app.models.outreach import Outreach
from app.models.website_audit import WebsiteAudit


def _make_session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine), engine


def test_parser_wires_all_commands():
    parser = cli.build_parser()

    args = parser.parse_args(["search", "--category", "plumber", "--city", "Austin"])
    assert args.func is cli.cmd_search
    assert args.category == "plumber"
    assert args.save is False

    args = parser.parse_args(["audit", "abc-123"])
    assert args.func is cli.cmd_audit
    assert args.business_id == "abc-123"

    args = parser.parse_args(["audit-all"])
    assert args.func is cli.cmd_audit_all

    args = parser.parse_args(["score-all"])
    assert args.func is cli.cmd_score_all

    args = parser.parse_args(["generate-outreach", "abc-123", "--angle", "AI_CHATBOT"])
    assert args.func is cli.cmd_generate_outreach
    assert args.angle == "AI_CHATBOT"

    args = parser.parse_args(["export", "out.csv"])
    assert args.func is cli.cmd_export
    assert args.path == "out.csv"


def test_cmd_export_writes_csv(tmp_path, monkeypatch):
    session_factory, engine = _make_session_factory()
    session = session_factory()
    session.add(Business(name="ABC Plumbing", city="Houston"))
    session.commit()
    session.close()

    monkeypatch.setattr(cli, "SessionLocal", session_factory)

    out_path = tmp_path / "export.csv"
    args = cli.build_parser().parse_args(["export", str(out_path)])
    args.func(args)

    with open(out_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["name"] == "ABC Plumbing"

    engine.dispose()


def test_cmd_audit_saves_new_audit_row(monkeypatch):
    session_factory, engine = _make_session_factory()
    session = session_factory()
    business = Business(name="ABC Plumbing", city="Houston", website="https://abcplumbing.com")
    session.add(business)
    session.commit()
    business_id = business.id
    session.close()

    monkeypatch.setattr(cli, "SessionLocal", session_factory)
    monkeypatch.setattr(
        cli,
        "run_audit",
        lambda business: {
            "url": business.website,
            "http_status": 200,
            "quality_category": "GOOD",
            "opportunity_types": ["AI_CHATBOT"],
            "opportunity_reasons": ["No chatbot found."],
            "ai_opportunity_score": 60,
            "redesign_opportunity_score": 20,
            "overall_opportunity_score": 40,
        },
    )

    args = cli.build_parser().parse_args(["audit", business_id])
    args.func(args)

    verify = session_factory()
    audits = verify.query(WebsiteAudit).filter_by(business_id=business_id).all()
    assert len(audits) == 1
    assert audits[0].overall_opportunity_score == 40
    assert verify.get(Business, business_id).website_status == "exists"
    verify.close()
    engine.dispose()


def test_cmd_generate_outreach_creates_row_with_no_prior_audit(monkeypatch):
    session_factory, engine = _make_session_factory()
    session = session_factory()
    business = Business(name="ABC Plumbing", city="Houston")
    session.add(business)
    session.commit()
    business_id = business.id
    session.close()

    monkeypatch.setattr(cli, "SessionLocal", session_factory)
    monkeypatch.setattr(
        cli,
        "generate_outreach_draft",
        lambda **kwargs: {"angle": "NEW_WEBSITE", "subject": "Quick idea", "body": "Hi there", "generated_by": "template"},
    )

    args = cli.build_parser().parse_args(["generate-outreach", business_id])
    args.func(args)

    verify = session_factory()
    outreach_rows = verify.query(Outreach).filter_by(business_id=business_id).all()
    assert len(outreach_rows) == 1
    assert outreach_rows[0].subject == "Quick idea"
    verify.close()
    engine.dispose()


def test_cmd_audit_unknown_business_exits_nonzero(monkeypatch, capsys):
    session_factory, engine = _make_session_factory()
    monkeypatch.setattr(cli, "SessionLocal", session_factory)

    args = cli.build_parser().parse_args(["audit", "does-not-exist"])
    try:
        args.func(args)
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1

    engine.dispose()
