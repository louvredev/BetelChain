from pydantic_settings import BaseSettings
from pydantic import Field
import json

class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    
    model_path: str = Field(default="models/model_svm_karung.joblib")
    meta_path: str = Field(default="models/model_meta.json")
    features_path: str = Field(default="models/extract_features.dill")
    
    cors_origins: str = Field(
        default='["http://localhost:3000", "http://localhost:5173"]'
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list:
        try:
            if isinstance(self.cors_origins, str):
                return json.loads(self.cors_origins)
            return self.cors_origins
        except:
            return ["http://localhost:3000", "http://localhost:5173"]

settings = Settings()

if settings.DEBUG:
    print("\n" + "="*60)
    print("⚙️  Configuration Loaded:")
    print("="*60)
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"MODEL_PATH: {settings.model_path}")
    print(f"META_PATH: {settings.meta_path}")
    print(f"FEATURES_PATH: {settings.features_path}")
    print(f"SUPABASE_URL: {settings.supabase_url[:30]}..." if settings.supabase_url else "SUPABASE_URL: NOT SET")
    print(f"CORS_ORIGINS: {settings.cors_origins_list}")
    print("="*60 + "\n")

