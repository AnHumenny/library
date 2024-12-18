from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
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
    date_created = Column(DateTime)

class DUser(Model):
    __tablename__ = "user"
    username = Column(String(50), unique=True)
    password = Column(String(100))

class DTest(Model):
    __tablename__ = "test"
    date_created = Column(DateTime(), nullable=True, default=datetime.utcnow)
    title = Column(String(100))
    autor = Column(String(100))
    category = Column(String(100))
    describe = Column(String(1000), nullable=True, default='')
    hashed = Column(String(200))


