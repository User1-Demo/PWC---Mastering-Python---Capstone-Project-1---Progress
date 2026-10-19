import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL)


async def main():
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT current_database(), current_user")
        )
        print(result.fetchone())

    await engine.dispose()


asyncio.run(main())