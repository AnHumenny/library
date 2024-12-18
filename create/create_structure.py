import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from shemas.database import DBook, DUser
from sqlalchemy import text
from dotenv import load_dotenv
import os
load_dotenv()

engine_base = create_async_engine(f"mysql+asyncmy://{os.getenv('user')}:{os.getenv('password')}"
                             f"@{os.getenv('host')}/", echo=True)
engine = create_async_engine(f"mysql+asyncmy://{os.getenv('user')}:{os.getenv('password')}"
                                   f"@{os.getenv('host')}/{os.getenv('database')}", echo=True)

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def create_database_if_not_exists():
    async with engine_base.begin() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {os.getenv('database')}"))

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(DBook.metadata.create_all)
        await conn.run_sync(DUser.metadata.create_all)

async def main():
    await create_database_if_not_exists()
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main())
