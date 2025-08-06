import os
import sys
from typing import Optional, Dict, List
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.topic_prompt import get_topic_prompt
from services.gemini import generate
from agents.base_agent import BaseAgent
from utils.validators import validate_topic_content

class TopicAgent(BaseAgent):
    """Konu anlatımı için özelleşmiş agent"""
    
    def __init__(self):
        super().__init__(get_topic_prompt(), "TopicAgent")
        self.topic_hierarchy = {}
        
    def process(self, 
                topic: str, 
                depth_level: str = "detailed",
                include_examples: bool = True) -> str:
        """
        Konu başlığı alır, detaylı açıklama üretir.
        
        Args:
            topic: Konu başlığı veya açıklaması
            depth_level: Detay seviyesi (basic, detailed, comprehensive)
            include_examples: Örnekler eklensin mi?
            
        Returns:
            Yapılandırılmış konu anlatımı
        """
        if not self.validate_input(topic):
            raise ValueError("Invalid topic provided")
            
        self.logger.info(f"Explaining topic: {topic} at {depth_level} level")
        
        message = self.build_message(
            topic,
            metadata={
                "depth": depth_level,
                "examples": include_examples
            }
        )
        
        explanation = generate(message)
        
        # İçeriği yapılandır ve doğrula
        structured_content = self._structure_content(explanation, topic)
        
        if validate_topic_content(structured_content):
            self._update_topic_hierarchy(topic, structured_content)
            return structured_content
        else:
            self.logger.error("Topic content validation failed")
            raise ValueError("Invalid topic content format")
    
    def get_subtopics(self, main_topic: str) -> List[str]:
        """Ana konunun alt konularını döndürür"""
        if main_topic in self.topic_hierarchy:
            return self.topic_hierarchy[main_topic].get("subtopics", [])
        return []
    
    def create_topic_outline(self, topic: str) -> Dict[str, List[str]]:
        """Konu için anahat oluşturur"""
        outline = {
            "introduction": [],
            "main_concepts": [],
            "examples": [],
            "summary": []
        }
        # Konu içeriğini analiz et ve anahat oluştur
        return outline
    
    def _structure_content(self, raw_content: str, topic: str) -> str:
        """Ham içeriği yapılandırır"""
        # Başlıklar, alt başlıklar, örnekler vb. düzenle
        # Hiyerarşik yapı oluştur
        return raw_content
    
    def _update_topic_hierarchy(self, topic: str, content: str):
        """Konu hiyerarşisini günceller"""
        # Alt konuları, ilişkili konuları vb. çıkar ve sakla
        pass