from fastapi import FastAPI
from sqlalchemy import text

from src.app.routes.claims import router as claims_router
from src.app.routes.policies import router as policies_router
from src.app.routes.users import router as users_router
from src.app.routes import auth
from src.app.routes.audit import router as audit_router
from src.app.db.session import engine
from src.app.routes import analytics
from src.app.routes.document import router as documents_router
from src.app.routes.ai import router as ai_router

app = FastAPI(
    title="Meridian ClaimIQ",
    version="1.0.0",
    description="Policy and claims management platform",
)

app.include_router(auth.router)
app.include_router(users_router)
app.include_router(policies_router)
app.include_router(claims_router)
app.include_router(audit_router)
app.include_router(analytics.router)
app.include_router(documents_router)
app.include_router(ai_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "meridian-insurance-api",
    }


@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "database_type": "postgresql",
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "unavailable",
        }