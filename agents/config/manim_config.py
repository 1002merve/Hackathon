from manim import config, WHITE, BLACK, RED, GREEN, BLUE, YELLOW
from pathlib import Path

class ManimConfig:
    """Manim yapılandırma ayarları"""
    
    def __init__(self):
        self.setup_defaults()
    
    def setup_defaults(self):
        """Varsayılan Manim ayarlarını yapılandırır"""
        # Genel ayarlar
        config.pixel_height = 1080
        config.pixel_width = 1920
        config.frame_rate = 60
        config.background_color = "#e0e6e2"
        
        # Renk paleti
        self.color_palette = {
            "primary": "#2E86AB",
            "secondary": "#A23B72",
            "accent": "#F18F01",
            "success": "#6A994E",
            "warning": "#F77F00",
            "error": "#D62828",
            "background": "#e0e6e2",
            "text": "#1A1A1A"
        }
        
        # Stil ayarları
        self.text_config = {
            "font": "Arial",
            "color": self.color_palette["text"],
            "font_size": 36
        }
        
        self.math_config = {
            "color": self.color_palette["primary"],
            "font_size": 42
        }
        
        # Animasyon ayarları
        self.animation_config = {
            "default_run_time": 1.5,
            "fade_time": 0.5,
            "wait_time": 1.0
        }
    
    def get_scene_config(self, scene_type: str) -> dict:
        """Sahne tipine göre özel yapılandırma döndürür"""
        configs = {
            "intro": {
                "background_color": self.color_palette["primary"],
                "text_color": WHITE,
                "animation_style": "dramatic"
            },
            "solution": {
                "background_color": self.color_palette["background"],
                "text_color": self.color_palette["text"],
                "animation_style": "educational"
            },
            "topic": {
                "background_color": self.color_palette["background"],
                "text_color": self.color_palette["text"],
                "animation_style": "explanatory"
            },
            "outro": {
                "background_color": self.color_palette["secondary"],
                "text_color": WHITE,
                "animation_style": "celebratory"
            }
        }
        return configs.get(scene_type, configs["solution"])
    
    def apply_theme(self, theme_name: str):
        """Önceden tanımlı tema uygular"""
        themes = {
            "dark": {
                "background": "#1a1a1a",
                "text": "#ffffff",
                "primary": "#3498db",
                "secondary": "#e74c3c"
            },
            "light": {
                "background": "#ffffff",
                "text": "#333333",
                "primary": "#2980b9",
                "secondary": "#c0392b"
            },
            "educational": {
                "background": "#f8f9fa",
                "text": "#212529",
                "primary": "#0066cc",
                "secondary": "#28a745"
            }
        }
        
        if theme_name in themes:
            self.color_palette.update(themes[theme_name])
            config.background_color = self.color_palette["background"]