from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase

class Model(DeclarativeBase):
    """Base model"""
    id = Column(Integer, primary_key=True, autoincrement=True)

class DBook(Model):
    """Represents a book in the database.

        Attributes:
            title (str): Book title, max length 100 characters.
            autor (str): Book author, max length 100 characters.
            category (str): Book category, max length 100 characters.
            describe (str): Book description, max length 1000 characters, nullable with default empty string.
            hashed (str): Hashed value, max length 200 characters.
            date_created (DateTime): Date and time when the book was created.

        Table:
            book: The database table name.
        """
    __tablename__ = "book"
    title = Column(String(100))
    autor = Column(String(100))
    category = Column(String(100))
    describe = Column(String(1000), nullable=True, default='')
    hashed = Column(String(200))
    date_created = Column(DateTime)

class DUser(Model):
    """Represents a user in the database.

        Attributes:
            username (str): Unique username of the user, max length 50 characters.
            password (str): Hashed password of the user, max length 100 characters.

        Table:
            user: The database table name.
        """
    __tablename__ = "user"
    username = Column(String(50), unique=True)
    password = Column(String(100))
