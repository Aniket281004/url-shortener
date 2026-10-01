from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr

from app.database import engine, Base, get_db
from app import models, crud, auth
from app.schemas import UrlCreate

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Multi-Tenant URL Shortener", version="3.0.0", lifespan=lifespan)

def require_same_origin(request: Request):
    origin = request.headers.get("origin")
    parsed = urlsplit(origin or "")
    if (not parsed.scheme or parsed.scheme != request.url.scheme
            or parsed.netloc.lower() != request.headers.get("host", "").lower()):
        raise HTTPException(status_code=403, detail="Invalid request origin")


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
def register_tenant(data: TenantRegister, request: Request, db: Session = Depends(get_db)):
    require_same_origin(request)
    existing = db.query(models.Tenant).filter(models.Tenant.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.hash_password(data.password)
    tenant = models.Tenant(name=data.name, email=data.email, hashed_password=hashed_pw)
    try:
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"message": "Tenant registered successfully", "tenant_id": tenant.id}

@app.post("/auth/login")
def login_tenant(data: TenantLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    require_same_origin(request)
    tenant = db.query(models.Tenant).filter(models.Tenant.email == data.email).first()
    if not tenant or not auth.verify_password(data.password, tenant.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"tenant_id": tenant.id, "email": tenant.email})
    response.set_cookie(
        "linklet_token", access_token, httponly=True, secure=auth.COOKIE_SECURE,
        samesite="lax", max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/"
    )
    return {"message": "Logged in"}

@app.get("/auth/status")
def auth_status(current_tenant: models.Tenant = Depends(auth.get_current_tenant)):
    return {"authenticated": True}

@app.post("/auth/logout")
def logout(request: Request, response: Response):
    require_same_origin(request)
    response.delete_cookie("linklet_token", path="/", httponly=True, secure=auth.COOKIE_SECURE, samesite="lax")
    return {"message": "Logged out"}

@app.post("/shorten", status_code=201)
def create_short_url(
    item: UrlCreate,
    request: Request,
    current_tenant: models.Tenant = Depends(auth.get_current_tenant),
    db: Session = Depends(get_db)
):
    require_same_origin(request)
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
