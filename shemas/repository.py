from sqlalchemy import select, insert, asc, delete, and_
from sqlalchemy.exc import NoResultFound, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from shemas.database import DBook, DUser
import os
from dotenv import load_dotenv
load_dotenv()


engine = create_async_engine(f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
                                   f"@{os.getenv('DB_HOST')}/{os.getenv('DB_DATABASE')}", echo=True)


new_session = async_sessionmaker(engine, expire_on_commit=False)


class Repo:
    @classmethod
    async def select_all_book(cls):
        async with new_session() as session:
            q = select(DBook)
            result = await session.execute(q)
            answer = result.scalars().all()
            return answer

    @classmethod
    async def sorted_category(cls):
        async with new_session() as session:
            q = select(DBook).order_by(asc(DBook.category))
            result = await session.execute(q)
            answer = result.scalars().all()
            await session.close()
            return answer

    @classmethod
    async def sorted_autor(cls):
        async with new_session() as session:
            q = select(DBook).order_by(asc(DBook.autor))
            result = await session.execute(q)
            answer = result.scalars().all()
            await session.close()
            return answer

    @classmethod
    async def insert_new_book(cls, l):
        async with new_session() as session:
            q = insert(DBook).values(l)
            await session.execute(q)
            await session.commit()
            await session.close()
            return

    @classmethod
    async def drop_file(cls, ssid):
        async with new_session() as session:
            try:
                query = select(DBook).where(DBook.id == int(ssid))
                result = await session.execute(query)
                record = result.scalar_one_or_none()
                if record is None:
                    return False
                delete_query = delete(DBook).where(DBook.id == int(ssid))
                await session.execute(delete_query)
                await session.commit()
                return
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

