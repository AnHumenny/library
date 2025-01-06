import asyncio
import hashlib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from shemas.database import DBook, DUser
from sqlalchemy import text, select
from dotenv import load_dotenv
from shemas.repository import engine
import os
load_dotenv()


engine_base = create_async_engine(
    f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/",
    echo=True
)


async def create_database_if_not_exists():
    try:
        async with engine_base.connect() as conn:
            await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_DATABASE')}"))
            await conn.commit()
            print("База данных успешно создана или уже существует.")
    except Exception as e:
        print(f"Произошла ошибка при создании базы данных: {e}")
    finally:
        await engine_base.dispose()


async def create_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(DBook.metadata.create_all)
            await conn.run_sync(DUser.metadata.create_all)
            print("Таблицы успешно созданы.")
    except SQLAlchemyError as e:
        print(f"Произошла ошибка при создании таблиц: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(username, password):
    try:
        hashed_password = hash_password(password)
        async with AsyncSession(engine) as session:
            async with session.begin():
                result = await session.execute(select(DUser).where(DUser.username == username))
                existing_user = result.scalars().first()
                if existing_user:
                    print(f"Пользователь с именем '{username}' уже существует.")
                    return
                new_user = DUser(username=username, password=hashed_password)
                session.add(new_user)
                print(f"Пользователь '{username}' успешно создан.")
    except SQLAlchemyError as e:
        print(f"Ошибка при работе с базой данных: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


async def main():
    await create_database_if_not_exists()
    await create_tables()
    await create_user(os.getenv("user"), os.getenv("password"))


if __name__ == "__main__":
    asyncio.run(main())
