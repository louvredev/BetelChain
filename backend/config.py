from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # FastAPI
    environment: str = "development"
    debug: bool = True
    
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # Model
    model_path: str = "models/model_package_v2.pkl"
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://betel-chain.vercel.app"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()

