from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.session import engine
from app.models.base import Base
import app.models.span as span_model
import app.models.trace as trace_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on server startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    yield


app = FastAPI(
    title="Chronos API",
    description="Backend API for the Chronos project",
    version="0.1.0",
    lifespan=lifespan,
)


# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev environments; adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to Chronos API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

