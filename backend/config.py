# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str  # Ini case-sensitive!
    supabase_anon_key: str
    supabase_service_role_key: str
    model_path: str = "models/model_svm_karung.joblib"
    meta_path: str = "models/model_meta.json"


    class Config:
        env_file = ".env"

settings = Settings()

