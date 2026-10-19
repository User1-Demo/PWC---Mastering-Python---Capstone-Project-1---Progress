from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    analytics,
    audit,
    auth,
    claims,
    documents,
    policies,
    regions,
    users,
)

api_router = APIRouter()
for module in (users, auth, regions, policies, claims, documents, ai, analytics, audit):
    api_router.include_router(module.router)
