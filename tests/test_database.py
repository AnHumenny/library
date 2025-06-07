import sys
import os

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
async def test_db_engine():
    engine = create_async_engine(
        f"mysql+asyncmy://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/test_db",
        echo=True
    )

    async with engine.connect() as conn:
        await conn.execute(text("CREATE DATABASE IF NOT EXISTS test_db"))
        await conn.commit()

    yield engine

    async with engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS test_db"))
        await conn.commit()

    await engine.dispose()