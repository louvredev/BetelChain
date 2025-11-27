from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from models.sack_detector import get_detector
from routers import detect, harvest

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*60)
    print("🚀 BETELCHAIN ML SERVICE STARTING...")
    print("="*60)
    
    try:
        detector = get_detector(
            settings.model_path,
            settings.meta_path
        )
        print("\n✅ ML Model ready!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    yield
    
    print("\n🛑 Shutdown\n")

app = FastAPI(
    title="BetelChain ML Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Atau list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router)
app.include_router(harvest.router)

@app.get("/")
def root():
    return {"service": "BetelChain ML", "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

