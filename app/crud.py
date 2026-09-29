from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models
from app.utils import generate_short_code

def create_short_url(db:Session,original_url:str)->models.URLItem:
    short_code = generate_short_code()
    db_item = models.URLItem(original_url = original_url,short_code=short_code)
    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
    except IntegrityError:
        db.rollback()
        short_code = generate_short_code()
        db_item = models.URLItem(original_url = original_url,short_code=short_code)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
    return db_item

def get_and_increment_url(db:Session,short_code:str) -> models.URLItem |None:
    db_item = db.query(models.URLItem).filter(models.URLItem.short_code == short_code).first()
    if db_item:
        db.commit()
        db.refresh(db_item)
    return db_item