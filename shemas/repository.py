from sqlalchemy import select, insert, asc, delete, and_, desc, func
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
    async def select_all_book(cls, session: AsyncSession, page: int, per_page: int):
        offset = (page - 1) * per_page
        q = select(DBook).order_by(desc(DBook.id)).offset(offset).limit(per_page)
        result = await session.execute(q)
        return result.scalars().all()

    @classmethod
    async def count_books(cls, session: AsyncSession):
        q = select(func.count()).select_from(DBook)
        result = await session.execute(q)
        return result.scalar_one()

    @classmethod
    async def sorted_category(cls, session: AsyncSession, page: int, per_page: int):
        offset = (page - 1) * per_page
        q = select(DBook).order_by(desc(DBook.category)).offset(offset).limit(per_page)
        result = await session.execute(q)
        return result.scalars().all()

    @classmethod
    async def sorted_autor(cls, session: AsyncSession, page: int, per_page: int):
        offset = (page - 1) * per_page
        q = select(DBook).order_by(desc(DBook.autor)).offset(offset).limit(per_page)
        result = await session.execute(q)
        return result.scalars().all()

    @classmethod
    async def insert_new_book(cls, l):
        async with new_session() as session:
            async with session.begin():
                try:
                    q = insert(DBook).values(l)
                    await session.execute(q)
                    await session.commit()
                    return
                except Exception as e:
                    await session.rollback()
                    raise e

    @classmethod
    async def drop_file(cls, ssid):
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
        if not search:
            return "Ошибка при поиске книг"
        async with new_session() as session:
            try:
                if temp == "title":
                    q = select(DBook).where(DBook.title.like(f"%{search}%"))
                if temp == "category":
                    q = select(DBook).where(DBook.category.like(f"%{search}%"))
                if temp == "author":
                    q = select(DBook).where(DBook.autor.like(f"%{search}%"))
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
        async with new_session() as session:
            q = select(DUser).where(and_(DUser.username == username, DUser.password == password))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return True

