from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import engine, Base, get_db
from app import models, crud, auth
from app.schemas import UrlCreate

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Multi-Tenant URL Shortener", version="3.0.0", lifespan=lifespan)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(Path(__file__).resolve().parent.parent / "frontend" / "index.html")

class TenantRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class TenantLogin(BaseModel):
    email: EmailStr
    password: str

@app.post("/auth/register", status_code=201)
def register_tenant(data: TenantRegister, db: Session = Depends(get_db)):
    existing = db.query(models.Tenant).filter(models.Tenant.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.hash_password(data.password)
    tenant = models.Tenant(name=data.name, email=data.email, hashed_password=hashed_pw)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"message": "Tenant registered successfully", "tenant_id": tenant.id}

@app.post("/auth/login")
def login_tenant(data: TenantLogin, db: Session = Depends(get_db)):
    tenant = db.query(models.Tenant).filter(models.Tenant.email == data.email).first()
    if not tenant or not auth.verify_password(data.password, tenant.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"tenant_id": tenant.id, "email": tenant.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/shorten", status_code=201)
def create_short_url(
    item: UrlCreate,
    request: Request,
    current_tenant: models.Tenant = Depends(auth.get_current_tenant),
    db: Session = Depends(get_db)
):
    db_item = crud.create_tenant_short_url(db, current_tenant.id, str(item.url))
    base_url = str(request.base_url)
    return {
        "short_code": db_item.short_code,
        "short_url": f"{base_url}{db_item.short_code}",
        "tenant_id": current_tenant.id
    }

@app.get("/my-urls")
def list_tenant_urls(
    current_tenant: models.Tenant = Depends(auth.get_current_tenant),
    db: Session = Depends(get_db)
):
    return db.query(models.URLItem).filter(models.URLItem.tenant_id == current_tenant.id).all()

@app.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    db_item = crud.get_and_increment_url(db, short_code)
    if not db_item:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=db_item.original_url, status_code=302)
