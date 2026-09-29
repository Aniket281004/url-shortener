from sqlalchemy.orm import Session
from sqlalchemy import update
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

def create_tenant_short_url(db: Session, tenant_id: int, original_url: str) -> models.URLItem:
    for _ in range(5):
        db_item = models.URLItem(tenant_id=tenant_id, original_url=original_url, short_code=generate_short_code())
        db.add(db_item)
        try:
            db.commit()
            db.refresh(db_item)
            return db_item
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Could not generate a unique short code")

def get_and_increment_url(db:Session,short_code:str) -> models.URLItem |None:
    result = db.execute(update(models.URLItem).where(models.URLItem.short_code == short_code).values(clicks=models.URLItem.clicks + 1))
    if not result.rowcount:
        db.rollback()
        return None
    db.commit()
    return db.query(models.URLItem).filter(models.URLItem.short_code == short_code).first()
