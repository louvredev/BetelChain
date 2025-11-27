from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True
    
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    model_path: str = "models/model_svm_karung.joblib"
    meta_path: str = "models/model_meta.json"
    
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://betel-chain.vercel.app"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()

