import os
import sys
from typing import Optional, Dict, List
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.solution_prompt import get_solution_prompt
from services.gemini import generate
from agents.base_agent import BaseAgent
from utils.validators import validate_solution_format

class SolutionAgent(BaseAgent):
    """Soru çözüm üretimi için özelleşmiş agent"""
    
    def __init__(self):
        super().__init__(get_solution_prompt(), "SolutionAgent")
        self.solution_cache = {}
        
    def process(self, 
                question: str, 
                image_b64: Optional[str] = None, 
                pdf_b64: Optional[str] = None,
                difficulty_level: str = "medium") -> str:
        """
        Soru metni ve opsiyonel görsel/pdf ile detaylı çözüm üretir.
        
        Args:
            question: Soru metni
            image_b64: Base64 kodlanmış görsel
            pdf_b64: Base64 kodlanmış PDF
            difficulty_level: Zorluk seviyesi (easy, medium, hard)
            
        Returns:
            Yapılandırılmış çözüm metni
        """
        if not self.validate_input(question):
            raise ValueError("Invalid question provided")
            
        # Cache kontrolü
        cache_key = self._generate_cache_key(question, image_b64, pdf_b64)
        if cache_key in self.solution_cache:
            self.logger.info("Returning cached solution")
            return self.solution_cache[cache_key]
            
        self.logger.info(f"Solving question with difficulty: {difficulty_level}")
        
        message = self.build_message(
            question, 
            image_b64=image_b64, 
            pdf_b64=pdf_b64,
            metadata={"difficulty": difficulty_level}
        )
        
        solution = generate(message)
        
        # Çözümü yapılandır ve doğrula
        structured_solution = self._structure_solution(solution)
        
        if validate_solution_format(structured_solution):
            self.solution_cache[cache_key] = structured_solution
            return structured_solution
        else:
            self.logger.error("Solution format validation failed")
            raise ValueError("Invalid solution format")
    
    def get_solution_steps(self, solution: str) -> List[Dict[str, str]]:
        """Çözümü adımlara ayırır"""
        steps = []
        # Çözüm metnini parse et ve adımlara ayır
        # Her adım için başlık, açıklama, formül vb. bilgileri çıkar
        return steps
    
    def _generate_cache_key(self, question: str, image: Optional[str], pdf: Optional[str]) -> str:
        """Cache için unique key üretir"""
        import hashlib
        content = f"{question}_{bool(image)}_{bool(pdf)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _structure_solution(self, raw_solution: str) -> str:
        """Ham çözümü yapılandırır"""
        # Başlıklar, adımlar, formüller vb. düzenle
        # Markdown formatına dönüştür
        return raw_solution