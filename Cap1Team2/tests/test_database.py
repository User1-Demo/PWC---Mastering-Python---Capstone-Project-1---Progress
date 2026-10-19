from sqlalchemy import text

from claimiq.db.database import engine


def test_real_database_connection() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1