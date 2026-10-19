from fastapi import APIRouter
from sqlalchemy import text

from src.db.session import engine

router = APIRouter()


@router.get("/db-health")
def db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {"database": "connected"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise