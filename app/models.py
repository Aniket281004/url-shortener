from sqlalchemy import Column,Integer,String ,DateTime,func
from app.database import Base

class URLItem(Base):
    __tablename__ = "urls"
    id = Column(Integer,primary_key = True,index = True)
    original_url = Column(String,nullable = False)
    short_code = Column(String(10),unique=True,index = True,nullable = False)
    created_at = Column(DateTime(timezone = True),server_default = func.now())