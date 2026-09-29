from pydantic import BaseModel, ConfigDict, HttpUrl


class UrlCreate(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    short_url: str
    original_url: str
    clicks: int
