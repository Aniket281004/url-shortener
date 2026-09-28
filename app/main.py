from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import RedirectResponse
from app.database import init_db
from app.schemas import UrlCreate
from app import crud
@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db()
    yield
app = FastAPI(
    title="Url Shortener API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "URL Shortener API is running. Go to /docs for API documentation."}

@app.post("/shorten",status_code = 201)
def shorten_url(item:UrlCreate,request:Request):
    short_code = crud.create_short_url(str(item.url))
    base_url = str(request.base_url)
    return {
        "short_code":short_code,
        "short_url":f"{base_url}{short_code}"
    }

@app.get("/{short_code}")
def redirect_to_url(short_code:str):
    original_url = crud.get_and_increment_url(short_code)
    if not original_url:
        raise HTTPException(status_code=404,detail="Short code not found")
    return RedirectResponse(url=original_url,status_code = 302)

