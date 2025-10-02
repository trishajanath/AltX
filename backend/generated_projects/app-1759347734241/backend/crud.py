from sqlalchemy.orm import Session
from . import models, schemas

def get_event(db: Session, event_id: int):
    return db.query(models.CollegeEvent).filter(models.CollegeEvent.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CollegeEvent).order_by(models.CollegeEvent.start_date.asc()).offset(skip).limit(limit).all()

def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.CollegeEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event