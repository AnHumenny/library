from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Model(DeclarativeBase):
    id = Column(Integer, primary_key=True, autoincrement=True)

class DBook(Model):
    __tablename__ = "book"
    title = Column(String(100))
    autor = Column(String(100))
    category = Column(String(100))
    describe = Column(String(1000), nullable=True, default='')
    hashed = Column(String(200))




