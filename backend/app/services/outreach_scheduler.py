"""Small in-process worker for active outreach batches.

One process owns one worker; deploy a single API worker or replace this with
the platform job runner when horizontally scaling. Each dispatch re-checks all
limits in the database, so an accidental second worker cannot exceed limits.
"""
import threading

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.outreach_batch import OutreachBatch

_stop = threading.Event()
_thread: threading.Thread | None = None


def _run() -> None:
    while not _stop.wait(60):
        db = SessionLocal()
        try:
            from app.api.gmail import dispatch_batch
            batch_ids = db.scalars(select(OutreachBatch.id).where(OutreachBatch.status == "ACTIVE")).all()
            for batch_id in batch_ids:
                try:
                    dispatch_batch(batch_id, db)
                except Exception:
                    # Individual errors (outside hours, no Gmail connection,
                    # provider failure) are recorded by dispatch/send where
                    # appropriate and must not stop later batches.
                    db.rollback()
        finally:
            db.close()


def start_scheduler() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_run, name="outreach-scheduler", daemon=True)
    _thread.start()


def stop_scheduler() -> None:
    _stop.set()
