import os
import sys
import re
from typing import Optional, Dict, List, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.code_prompt import get_manim_prompt
from prompts.scene_prompt import scene_combination_prompt
from services.gemini import generate
from agents.base_agent import BaseAgent
from utils.validators import validate_manim_code

class CodeAgent(BaseAgent):
    """Manim kod üretimi için özelleşmiş agent"""
    
    def __init__(self):
        super().__init__(get_manim_prompt(), "CodeAgent")
        self.scene_counter = 0
        
    def process(self, 
                question: str, 
                image_b64: Optional[str] = None,
                scene_type: str = "solution") -> str:
        """
        Soru metni ve opsiyonel görsel ile Manim video çözüm kodu üretir.
        
        Args:
            question: Soru metni veya konu açıklaması
            image_b64: Base64 kodlanmış görsel
            scene_type: Sahne tipi (solution, topic, intro, outro)
            
        Returns:
            Manim kodu
        """
        if not self.validate_input(question):
            raise ValueError("Invalid input provided")
            
        self.logger.info(f"Generating {scene_type} code for question")
        
        message = self.build_message(
            question, 
            image_b64=image_b64,
            metadata={"scene_type": scene_type}
        )
        
        code = generate(message)
        
        # Kodu temizle ve doğrula
        clean_code = self._extract_python_code(code)
        
        if validate_manim_code(clean_code):
            self.scene_counter += 1
            return self._enhance_code(clean_code, scene_type)
        else:
            self.logger.error("Generated code validation failed")
            raise ValueError("Invalid Manim code generated")
    
    def generate_combined_scenes(self, scenes: List[Tuple[str, str]]) -> str:
        """
        Birden fazla sahneyi birleştiren kod üretir.
        
        Args:
            scenes: (sahne_tipi, sahne_kodu) tuple listesi
            
        Returns:
            Birleştirilmiş Manim kodu
        """
        self.logger.info(f"Combining {len(scenes)} scenes")
        
        scene_descriptions = []
        for scene_type, code in scenes:
            scene_descriptions.append(f"Sahne Tipi: {scene_type}\nKod:\n{code}\n")
        
        combined_prompt = scene_combination_prompt.format(
            scenes="\n---\n".join(scene_descriptions)
        )
        
        message = {"text": combined_prompt, "image": "", "pdf": ""}
        combined_code = generate(message)
        
        return self._extract_python_code(combined_code)
    
    def _extract_python_code(self, response: str) -> str:
        """Yanıttan Python kodunu çıkarır"""
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return response.strip()
    
    def _enhance_code(self, code: str, scene_type: str) -> str:
        """Kodu sahne tipine göre geliştirir"""
        enhancements = {
            "intro": self._add_intro_elements,
            "outro": self._add_outro_elements,
            "solution": self._add_solution_elements,
            "topic": self._add_topic_elements
        }
        
        if scene_type in enhancements:
            return enhancements[scene_type](code)
        return code
    
    def _add_intro_elements(self, code: str) -> str:
        """Giriş sahnesi için eklemeler"""
        # Logo, başlık animasyonları vb. ekle
        return code
    
    def _add_outro_elements(self, code: str) -> str:
        """Çıkış sahnesi için eklemeler"""
        # Özet, teşekkür mesajı vb. ekle
        return code
    
    def _add_solution_elements(self, code: str) -> str:
        """Çözüm sahnesi için eklemeler"""
        # Adım numaraları, vurgular vb. ekle
        return code
    
    def _add_topic_elements(self, code: str) -> str:
        """Konu anlatım sahnesi için eklemeler"""
        # Başlıklar, alt başlıklar vb. ekle
        return code