# config/settings.py DOSYASINDAKİ DEĞİŞİKLİKLER

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # API Keys
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY") # YENİ EKLENDİ
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    upload_dir: Path = base_dir / "uploads"
    static_dir: Path = base_dir / "static"
    video_output_dir: Path = static_dir / "videomedia"
    temp_dir: Path = base_dir / "temp"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    # Video Settings
    default_video_quality: str = "1080p60"
    default_video_format: str = "mp4"
    max_video_duration: int = 600  # seconds
    
    # AI Settings
    llm_provider: str = Field("gemini", env="LLM_PROVIDER") 
    gemini_model: str = "gemini-2.5-pro" 
    openai_model: str = "gpt-4o-mini" #
    max_retries: int = 3
    timeout: int = 130
    
    # Cache Settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = base_dir / "logs" / "app.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Dizinleri oluştur
        self.upload_dir.mkdir(exist_ok=True)
        self.video_output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(exist_ok=True)