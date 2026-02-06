from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from auth.backend import JWTAuthBackend
from auth.dependencies import require_authenticated_user
from database.db import drop_db, init_db

app = FastAPI(
    title="Leave Query API",
    description="API for managing leave queries using AI",
    version="1.0.0",
    dependencies=[Depends(require_authenticated_user)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())

import ai.apis
import auth.apis
import organizations.apis
import users.apis


@app.on_event("startup")
def on_startup():
    init_db()


@app.delete("/admin/drop-db")
async def drop_database():
    drop_db()
    return {"status": "ok", "message": "Database tables dropped"}


@app.get("/")
async def root():
    return {
        "message": "Welcome to Leave Query API using AI",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
