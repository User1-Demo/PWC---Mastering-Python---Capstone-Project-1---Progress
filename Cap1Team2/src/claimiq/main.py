from fastapi import FastAPI

from claimiq.api.analytics import router as analytics_router
from claimiq.api.audit_logs import router as audit_logs_router
from claimiq.api.auth import router as auth_router
from claimiq.api.claim_notes import router as claim_notes_router
from claimiq.api.claims import router as claims_router
from claimiq.api.documents import router as documents_router
from claimiq.api.policies import router as policies_router
from claimiq.api.users import router as users_router
from claimiq.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Insurance claims and policy knowledge platform",
    version=settings.app_version,
)

app.include_router(analytics_router)
app.include_router(audit_logs_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(policies_router)
app.include_router(claims_router)
app.include_router(claim_notes_router)
app.include_router(documents_router)

@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}