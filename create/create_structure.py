import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from shemas.database import DBook, DUser
from sqlalchemy import text
from dotenv import load_dotenv
from shemas.repository import engine
import os
load_dotenv()

engine_base = create_async_engine(f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
                                   f"@{os.getenv('DB_HOST')}/", echo=True)


async def create_database_if_not_exists():
    async with engine_base.begin() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_DATABASE')}"))
        await conn.commit()
        await engine_base.dispose()

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(DBook.metadata.create_all)
        await conn.run_sync(DUser.metadata.create_all)

async def main():
    await create_database_if_not_exists()
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main())
