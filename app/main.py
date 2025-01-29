from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.models import User, Attendance
from app.api.v1 import user, auth, attendance, relationship
from app.api.v1.exception_handlers import add_exception_handlers
from app.core.logger import get_logger

import uvicorn

# Initialize logger
logger = get_logger("app.main")

# Create all tables
User.metadata.create_all(bind=engine)
Attendance.metadata.create_all(bind=engine)

app = FastAPI(
    title="Diploma FastAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from Next.js
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(attendance.router, prefix="/api/v1/attendances", tags=["attendances"])
app.include_router(relationship.router, prefix="/api/v1/relationships", tags=["relationships"])

add_exception_handlers(app)


# Health Check Endpoint
@app.get("/health", tags=["health"])
def health():
    return {"status": "OK"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
