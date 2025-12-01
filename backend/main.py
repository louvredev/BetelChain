from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from config import settings
from models.sack_detector import get_detector
from routers import detect, transactions, payments, farmers, ml_harvest, dashboard

logging.basicConfig(
    level="INFO" if not settings.DEBUG else "DEBUG",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*60)
    print("🚀 BETELCHAIN ML SERVICE STARTING...")
    print("="*60)
    
    try:
        detector = get_detector(
            settings.model_path,
            settings.meta_path,
            settings.features_path
        )
        print("\n✅ ML Model ready!")
        logger.info("ML model loaded successfully")
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        logger.error(f"Failed to load model: {e}")
        raise
    
    yield
    
    print("\n🛑 Shutdown\n")
    logger.info("Application shutdown")

app = FastAPI(
    title="BetelChain ML Service",
    description="API untuk detect warna karung dan harvest recording",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS enabled for origins: {settings.cors_origins_list}")

app.include_router(detect.router)
app.include_router(transactions.router)
app.include_router(payments.router)
app.include_router(farmers.router)
app.include_router(ml_harvest.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {
        "service": "BetelChain ML Service",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ml-detection"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

