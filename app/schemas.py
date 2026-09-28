from pydantic import BaseModel,HttpUrl
class UrlCreate(BaseModel):
    url:HttpUrl
class URLResponse(BaseModel):
    short_code:str
    short_url:str
    original_url:str
    clicks:int