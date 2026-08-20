from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.sender import Sender
from app.schemas.sender import SenderCreate, SenderRead

router = APIRouter(prefix="/api/senders", tags=["senders"])


@router.get("", response_model=list[SenderRead])
def list_senders(db: Session = Depends(get_db)):
    return db.scalars(select(Sender).order_by(Sender.name)).all()


@router.post("", response_model=SenderRead, status_code=201)
def create_sender(payload: SenderCreate, db: Session = Depends(get_db)):
    sender = Sender(**payload.model_dump())
    db.add(sender)
    db.commit()
    db.refresh(sender)
    return sender


@router.delete("/{sender_id}", status_code=204)
def delete_sender(sender_id: str, db: Session = Depends(get_db)):
    sender = db.get(Sender, sender_id)
    if not sender:
        raise HTTPException(404, "Sender not found")
    db.delete(sender)
    db.commit()
