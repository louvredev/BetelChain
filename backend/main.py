from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from models.sack_detector import get_detector
from routers import detect, harvest

# Startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model
    print("🚀 Loading ML model on startup...")
    try:
        detector = get_detector(settings.model_path)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="BetelChain ML Service",
    description="Machine Learning service untuk deteksi warna karung",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detect.router)
app.include_router(harvest.router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "service": "BetelChain ML Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

