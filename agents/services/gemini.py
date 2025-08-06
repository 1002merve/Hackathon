import base64
import os
from typing import Dict, Any, Optional, List
import asyncio
from google import genai
from google.genai import types
import backoff

from config import settings
from services.logger import get_logger
from services.openai import get_openai_service 
from services.openai import OpenAIService

class GeminiService:
    """Gemini API servis sınıfı"""
    
    def __init__(self):
        self.logger = get_logger("GeminiService")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=settings.max_retries
    )
    async def generate_async(self, message: Dict[str, Any]) -> str:
        """Asenkron içerik üretimi"""
        return await asyncio.to_thread(self.generate, message)
    
    def generate(self, message: Dict[str, Any]) -> str:
        """İçerik üretimi"""
        try:
            parts = self._build_parts(message)
            contents = [
                types.Content(
                    role="user",
                    parts=parts,
                ),
            ]
            
            tools = [
                types.Tool(googleSearch=types.GoogleSearch()),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                tools=tools,
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=63000,
            )
            
            result = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    result += chunk.text
            
            self.logger.info(f"Generated content length: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Generation error: {str(e)}")
            raise
    
    def _build_parts(self, message: Dict[str, Any]) -> List[types.Part]:
        """Mesaj parçalarını oluştur"""
        parts = []
        
        if isinstance(message, dict):
            # Text varsa ekle
            if 'text' in message and message['text']:
                parts.append(types.Part.from_text(text=message['text']))
            
            # Görsel varsa ekle
            if 'image' in message and message['image']:
                parts.append(types.Part.from_bytes(
                    mime_type="image/jpeg",
                    data=base64.b64decode(message['image'])
                ))
            
            # PDF varsa ekle
            if 'pdf' in message and message['pdf']:
                parts.append(types.Part.from_bytes(
                    mime_type="application/pdf",
                    data=base64.b64decode(message['pdf'])
                ))
        else:
            # String ise doğrudan text olarak ekle
            parts.append(types.Part.from_text(text=str(message)))
        
        return parts

# Global instance
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """Singleton Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

def generate(message: Dict[str, Any]) -> str:
    """
    Yapılandırmaya göre uygun LLM servisini seçer ve içerik üretir.
    Bu fonksiyon projenin geri kalanı için tek giriş noktasıdır.
    """
    print(message)
    provider = settings.llm_provider.lower()
    logger = get_logger("LLM_Dispatcher")
    
    logger.info(f"Routing request to LLM provider: {provider}")
    
    if provider == "openai":
        service = get_openai_service()
        return service.generate(message)
    elif provider == "gemini":
        service = get_gemini_service()
        return service.generate(message)
    else:
        error_msg = f"Unsupported LLM provider: '{settings.llm_provider}'. Supported providers are 'gemini' and 'openai'."
        logger.error(error_msg)
        raise ValueError(error_msg)