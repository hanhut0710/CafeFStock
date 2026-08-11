from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Ensure backend root directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base
from api.routes import router

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CafeF Stock Market Dashboard API",
    description="Backend API for local stock dashboard with automatic CafeF data refresh.",
    version="1.0.0"
)

# Configure CORS for local development (Vite runs on port 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok", "message": "CafeF Stock Dashboard API is running"}
