from sqlalchemy import select, insert, delete, and_, desc, func
from sqlalchemy.exc import NoResultFound, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from shemas.database import DBook, DUser
import os
from dotenv import load_dotenv
load_dotenv()


engine = create_async_engine(f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
                                   f"@{os.getenv('DB_HOST')}/{os.getenv('DB_DATABASE')}", echo=True)
new_session = async_sessionmaker(engine, expire_on_commit=False)


class Repo:

    @classmethod
    async def category(cls, session: AsyncSession):
        """Fetches unique categories from DBook table.

            Args:
                session (AsyncSession): Async SQLAlchemy session.

            Returns:
                list: Unique category values from DBook.

            Raises:
                SQLAlchemyError: If query execution fails.
                Exception: For unexpected errors.
            """
        q = select(DBook.category).distinct()
        result = await session.execute(q)
        return result.scalars().all()


    @classmethod
    async def count_books(cls, session: AsyncSession):
        """Counts the total number of books in the DBook table.

            Args:
                session (AsyncSession): Async SQLAlchemy session.

            Returns:
                int: Total count of books.

            Raises:
                SQLAlchemyError: If query execution fails.
                Exception: For unexpected errors.
            """
        q = select(func.count()).select_from(DBook)
        result = await session.execute(q)
        return result.scalar_one()


    @classmethod
    async def sorted_recent(cls, session: AsyncSession, page: int, per_page):
        """Fetches books sorted by recent ID with pagination.

            Args:
                cls: Class reference (unused).
                session (AsyncSession): Async SQLAlchemy session.
                page (int): Page number for pagination.
                per_page (int): Number of items per page.

            Returns:
                list: List of DBook objects sorted by ID in descending order.

            Raises:
                SQLAlchemyError: If query execution fails.
                Exception: For unexpected errors.
            """
        offset = (page - 1) * per_page
        q = select(DBook).order_by(desc(DBook.id)).offset(offset).limit(per_page)
        result = await session.execute(q)
        return result.scalars().all()


    @classmethod
    async def insert_new_book(cls, items):
        """Inserts a new book into the DBook table.

            Args:
                cls: Class reference (unused).
                items: Dictionary or list of dictionaries with book data to insert.

            Raises:
                Exception: If insertion fails, with rollback performed.
            """
        async with new_session() as session:
            async with session.begin():
                try:
                    q = insert(DBook).values(items)
                    await session.execute(q)
                    await session.commit()
                    return
                except Exception as e:
                    await session.rollback()
                    raise e


    @classmethod
    async def drop_file(cls, ssid):
        """Deletes a book record from the DBook table by ID.

            Args:
                cls: Class reference (unused).
                ssid: ID of the book record to delete (converted to int).

            Returns:
                str: Success message if deletion succeeds, error message if record not found,
                     False if an exception occurs.

            Raises:
                ValueError: If ssid cannot be converted to an integer.
                NoResultFound: If no record matches the given ID.
                IntegrityError: If deletion violates database constraints.
                SQLAlchemyError: If other database errors occur.
            """
        ssid = int(ssid)
        async with new_session() as session:
            try:
                query = select(DBook).where(DBook.id == int(ssid))
                result = await session.execute(query)
                record = result.scalar_one_or_none()
                if record is None:
                    return f"Файл с указанным идентификатором {ssid} не найден."
                delete_query = delete(DBook).where(DBook.id == int(ssid))
                await session.execute(delete_query)
                await session.commit()
                return f"Файл с указанным идентификатором {ssid} успешно удалён!"

            except (ValueError, NoResultFound, IntegrityError, SQLAlchemyError) as e:
                print("error", e)
                await session.rollback()
                return False


    @classmethod
    async def search_book(cls, search, temp):
        """Searches books in the DBook table based on a field and term.

            Args:
                cls: Class reference (unused).
                search: Search term to match (string).
                temp (str): Field to search in ('title', 'category', or 'author').

            Returns:
                list: List of matching DBook objects if found.
                str: Error message if search term is empty.
                None: If no results found.
                False: If an error occurs.

            Raises:
                ValueError: If search term processing fails.
                NoResultFound: If no records match.
                IntegrityError: If database constraint violation occurs.
                SQLAlchemyError: If other database errors occur.
            """
        if not search:
            return "Ошибка при поиске книг"
        async with new_session() as session:
            try:
                if temp == "title":
                    q = select(DBook).order_by(desc(DBook.id)).where(DBook.title.like(f"%{search}%"))
                if temp == "category":
                    q = select(DBook).order_by(desc(DBook.id)).where(DBook.category.like(f"%{search}%"))
                if temp == "author":
                    q = select(DBook).order_by(desc(DBook.id)).where(DBook.autor.like(f"%{search}%"))
                result = await session.execute(q)
                answer = result.scalars().all()
                await session.commit()
                if not answer:
                    return None
                return answer
            except ValueError:
                return False
            except NoResultFound:
                return False
            except IntegrityError:
                await session.rollback()
                return False
            except SQLAlchemyError:
                await session.rollback()
                return False


    @classmethod
    async def select_user(cls, username, password):
        """Checks if a user exists with the given username and password.

            Args:
                cls: Class reference (unused).
                username (str): Username to check.
                password (str): Password to check (expected to be hashed).

            Returns:
                bool: True if user exists with matching credentials, None if not found.

            Raises:
                SQLAlchemyError: If query execution fails.
                Exception: For unexpected errors.
            """
        async with new_session() as session:
            q = select(DUser).where(and_(DUser.username == username, DUser.password == password))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return True


    @classmethod
    async def all_query(cls, session: AsyncSession, page: int, per_page: int, link: str, name: str):
        """Fetches books from DBook with pagination, filtering, and sorting.

            Args:
                cls: Class reference (unused).
                session (AsyncSession): Async SQLAlchemy session.
                page (int): Page number for pagination.
                per_page (int): Number of items per page.
                link (str): Field name to sort by (e.g., 'title', 'author').
                name (str): Category name to filter by.

            Returns:
                list: List of DBook objects matching the filter and sort criteria.

            Raises:
                ValueError: If the specified sorting field is invalid.
                SQLAlchemyError: If query execution fails.
                Exception: For unexpected errors.
            """
        offset_value = (page - 1) * per_page
        order_field = getattr(DBook, link, None)
        if order_field is None:
            raise ValueError(f"Invalid field '{link}' for ordering")
        q = (select(DBook)
             .filter(DBook.category == name)
             .order_by(desc(order_field))
             .offset(offset_value)
             .limit(per_page))

        result = await session.execute(q)
        return result.scalars().all()


