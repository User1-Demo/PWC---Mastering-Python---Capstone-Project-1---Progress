from fastapi import FastAPI
from src.api.routes.health import router as health_router
from src.api.routes.users import router as users_router
from src.api.routes.policies import router as policy_router
from src.api.routes.claims import router as claims_router
from src.api.routes.auth import router as auth_router
from src.api.routes.documents import router as documents_router

app = FastAPI(title="ClaimIQ", version="1.0.0")

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(users_router)
app.include_router(policy_router)
app.include_router(claims_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {"message": "ClaimIQ API"}
