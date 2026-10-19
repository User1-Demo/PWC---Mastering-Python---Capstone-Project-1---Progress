"""
main.py

Purpose: The actual entrypoint of our FastAPI application.
This is what uvicorn runs to start the server.
"""

from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.policies.router import router as policies_router
from src.claims.router import router as claims_router
from src.documents.router import router as documents_router
from src.audit.router import router as audit_router
from src.ai_rag.router import router as ai_router

app = FastAPI(title="ClaimIQ API", version="0.1.0")

app.include_router(auth_router)
app.include_router(policies_router)
app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(audit_router)
app.include_router(ai_router)


@app.get("/")
def root():
    return {"message": "ClaimIQ API is running"}