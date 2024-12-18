import asyncio
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from shemas.database import  DUser
from sqlalchemy import select
from dotenv import load_dotenv
from create_structure import engine
load_dotenv()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def create_user(username, password):
    hashed_password = hash_password(password)  # хешируем пароль
    async with AsyncSession(engine) as session:
        async with session.begin():
            result = await session.execute(select(DUser).where(DUser.username == username))
            existing_user = result.scalars().first()
            if existing_user:
                print(f"Пользователь с именем '{username}' уже существует.")
                return
            new_user = DUser(username=username, password=hashed_password)
            session.add(new_user)

async def main():
    user = 'admin'
    password = 'admin'
    await create_user(user, password)

if __name__ == "__main__":
    asyncio.run(main())