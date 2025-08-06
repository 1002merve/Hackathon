from typing import List, Dict, Tuple, Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.code_agent import CodeAgent
from services.logger import get_logger

class SceneManager:
    """Video sahnelerini yöneten sınıf"""
    
    def __init__(self):
        self.logger = get_logger("SceneManager")
        self.code_agent = CodeAgent()
        self.scenes = []
        self.scene_order = []
        
    def create_intro_scene(self, title: str, subtitle: Optional[str] = None) -> str:
        """Giriş sahnesi oluşturur"""
        self.logger.info(f"Creating intro scene for: {title}")
        
        intro_content = f"""
        Başlık: {title}
        Alt Başlık: {subtitle or ""}
        Bu bir giriş sahnesi. Logo animasyonu, başlık efektleri ve 
        yumuşak geçişler kullan.
        """
        
        code = self.code_agent.process(intro_content, scene_type="intro")
        self.scenes.append(("intro", code))
        return code
    
    def create_content_scene(self, 
                           content: str, 
                           scene_type: str = "solution",
                           image_b64: Optional[str] = None) -> str:
        """İçerik sahnesi oluşturur (çözüm veya konu)"""
        self.logger.info(f"Creating {scene_type} scene")
        
        code = self.code_agent.process(content, image_b64, scene_type)
        self.scenes.append((scene_type, code))
        return code
    
    def create_transition_scene(self, 
                              from_scene: str, 
                              to_scene: str,
                              transition_text: Optional[str] = None) -> str:
        """Sahneler arası geçiş oluşturur"""
        self.logger.info(f"Creating transition from {from_scene} to {to_scene}")
        
        transition_content = f"""
        {from_scene} sahnesinden {to_scene} sahnesine geçiş.
        Geçiş metni: {transition_text or "Şimdi devam edelim..."}
        Yumuşak animasyonlar kullan.
        """
        
        code = self.code_agent.process(transition_content, scene_type="transition")
        self.scenes.append(("transition", code))
        return code
    
    def create_outro_scene(self, 
                         summary: Optional[str] = None,
                         call_to_action: Optional[str] = None) -> str:
        """Çıkış sahnesi oluşturur"""
        self.logger.info("Creating outro scene")
        
        outro_content = f"""
        Video Özeti: {summary or "Bu videoda öğrendiklerimiz..."}
        Çağrı: {call_to_action or "Abone olmayı unutmayın!"}
        Teşekkür mesajı ve logo ile bitir.
        """
        
        code = self.code_agent.process(outro_content, scene_type="outro")
        self.scenes.append(("outro", code))
        return code
    
    def combine_all_scenes(self) -> str:
        """Tüm sahneleri birleştirir"""
        if not self.scenes:
            raise ValueError("No scenes to combine")
            
        self.logger.info(f"Combining {len(self.scenes)} scenes")
        
        # Sahne sırasını optimize et
        self._optimize_scene_order()
        
        # Sahneleri birleştir
        combined_code = self.code_agent.generate_combined_scenes(self.scenes)
        
        return self._add_scene_management(combined_code)
    
    def _optimize_scene_order(self):
        """Sahne sırasını optimize eder"""
        # Intro her zaman başta
        # Outro her zaman sonda
        # Transition'lar uygun yerlerde
        # Content sahneleri mantıklı sırada
        pass
    
    def _add_scene_management(self, code: str) -> str:
        """Sahne yönetimi kodunu ekler"""
        management_code = """
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class ManagedVideo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="tr"))
        self.camera.background_color = "#e0e6e2"
        
        # Sahne listesi
        self.scenes = []
        
        # Sahneleri çalıştır
        for scene_method in self.scenes:
            scene_method()
            self.wait(0.5)  # Sahneler arası kısa bekleme
    
    def add_scene_transition(self, from_scene, to_scene):
        \"\"\"Sahneler arası yumuşak geçiş\"\"\"
        self.play(FadeOut(from_scene), FadeIn(to_scene), run_time=1)
"""
        return management_code + "\n\n" + code