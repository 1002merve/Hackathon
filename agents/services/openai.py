# YENİ DOSYA: services/openai.py

import base64
from typing import Dict, Any, List
import backoff
from openai import OpenAI

from config import settings
from services.logger import get_logger

class OpenAIService:
    """OpenAI API servis sınıfı"""

    def __init__(self):
        self.logger = get_logger("OpenAIService")
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is not set in settings.")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=settings.max_retries
    )
    def generate(self, message: Dict[str, Any]) -> str:
        """İçerik üretimi"""
        try:
            payload = self._build_payload(message)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=payload,
                temperature=0.3,
                max_tokens=4096,
            )
            
            result = response.choices[0].message.content or ""
            self.logger.info(f"Generated content length: {len(result)}")
            return result

        except Exception as e:
            self.logger.error(f"OpenAI generation error: {str(e)}")
            raise

    def _build_payload(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mesajı OpenAI API formatına dönüştürür"""
        content_parts = []
        
        # Text içeriği
        if 'text' in message and message['text']:
            content_parts.append({"type": "text", "text": message['text']})

        # Görsel içeriği (eğer varsa)
        if 'image' in message and message['image']:
            image_b64 = message['image']
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"
                }
            })
            
        # PDF içeriği - OpenAI chat modelleri doğrudan PDF almaz.
        # Bu nedenle bir uyarı logu basıp atlıyoruz.
        if 'pdf' in message and message['pdf']:
            self.logger.warning("PDF input is not directly supported by the OpenAI chat model and will be ignored.")

        return [{"role": "user", "content": content_parts}]

# Global instance
_openai_service = None

def get_openai_service() -> OpenAIService:
    """Singleton OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service