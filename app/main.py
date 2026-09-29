from contextlib import asynccontextmanager
from fastapi import Depends,FastAPI,HTTPException,Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import engine,Base,get_db
from app.schemas import UrlCreate
from app import crud

@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(
    title="Url Shortener API",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "URL Shortener API is running. Go to /docs for API documentation."}

@app.post("/shorten",status_code = 201)
def shorten_url(item:UrlCreate,request:Request,db:Session = Depends(get_db)):
    db_item = crud.create_short_url(db=db,original_url = str(item.url))
    base_url = str(request.base_url)
    return {
        "short_code":db_item.short_code,
        "short_url":f"{base_url}{db_item.short_code}"
    }

@app.get("/{short_code}")
def redirect_to_url(short_code:str,db:Session = Depends(get_db)):
    db_item = crud.get_and_increment_url(db = db,short_code=short_code)
    if not db_item:
        raise HTTPException(status_code=404,detail="Short code not found")
    return RedirectResponse(url=db_item.original_url,status_code = 302)

