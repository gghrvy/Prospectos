import pytest
from fastapi import HTTPException

from app.api.gmail import dispatch_batch
from app.models.outreach_batch import OutreachBatch


@pytest.mark.parametrize("status", ["PAUSED", "CANCELLED", "COMPLETE", "DRAFT"])
def test_dispatch_refuses_batch_that_is_not_active(db_session, status):
    batch = OutreachBatch(name="Paused run", status=status, timezone="UTC", send_hour_start=0, send_hour_end=24)
    db_session.add(batch)
    db_session.commit()

    with pytest.raises(HTTPException) as error:
        dispatch_batch(batch.id, db_session)

    assert error.value.status_code == 409
    db_session.refresh(batch)
    assert batch.status == status  # a refused dispatch must not flip it back to ACTIVE


def test_dispatch_route_is_not_shadowed_by_batch_controls(client):
    # POST /batches/{id}/dispatch must reach dispatch_batch, not the
    # pause/resume/cancel route that shares its path shape.
    response = client.post("/api/gmail/batches/missing-id/dispatch")

    assert response.status_code == 404
    assert response.json()["detail"] == "Batch not found"
