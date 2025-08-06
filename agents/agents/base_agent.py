from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
from services.logger import get_logger

class BaseAgent(ABC):
    """Tüm agentler için temel sınıf"""
    
    def __init__(self, prompt: str, agent_name: str):
        self.prompt = prompt
        self.agent_name = agent_name
        self.logger = get_logger(agent_name)
        
    def build_message(self, 
                     content: str, 
                     image_b64: Optional[str] = None, 
                     pdf_b64: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ortak mesaj yapısını oluşturur.
        
        Args:
            content: Ana içerik (soru, konu vb.)
            image_b64: Base64 kodlanmış görsel
            pdf_b64: Base64 kodlanmış PDF
            metadata: Ek bilgiler
            
        Returns:
            Yapılandırılmış mesaj dictionary
        """
        message = {
            "text": self.prompt.format(content=content),
            "image": image_b64 or "",
            "pdf": pdf_b64 or "",
            "metadata": metadata or {}
        }
        
        self.logger.info(f"Message built with content length: {len(content)}")
        return message
    
    @abstractmethod
    def process(self, *args, **kwargs) -> str:
        """Her agent'in implement etmesi gereken metod"""
        pass
    
    def validate_input(self, content: str) -> bool:
        """Girdi doğrulama"""
        if not content or not content.strip():
            self.logger.error("Empty content provided")
            return False
        return True