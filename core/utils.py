import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Global değişkenler
GEMINI_AVAILABLE = False
GEMINI_CLIENT = None

# Gemini kütüphanesini import etmeyi dene
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    logger.info("Google GenAI library imported successfully")
except ImportError as e:
    logger.error(f"Google GenAI library not available: {e}")
    logger.error("Please install: pip install google-genai")

def initialize_gemini_client():
    """Gemini client'ını başlat"""
    global GEMINI_CLIENT
    
    if not GEMINI_AVAILABLE:
        logger.error("Gemini library not available")
        return None
    
    if GEMINI_CLIENT is not None:
        return GEMINI_CLIENT
    
    try:
        # API key'i al
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.error("GEMINI_API_KEY not found in Django settings")
            return None
        
        if len(api_key.strip()) < 10:
            logger.error(f"GEMINI_API_KEY seems invalid (length: {len(api_key)})")
            return None
        
        # Client'ı oluştur
        GEMINI_CLIENT = genai.Client(api_key=api_key.strip())
        logger.info("Gemini client initialized successfully")
        return GEMINI_CLIENT
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None

class GeminiChatService:
    def __init__(self):
        self.client = initialize_gemini_client()
        # Mevcut modelleri dene
        self.models = [
            'gemini-1.5-flash',
            'gemini-1.5-pro', 
            'gemini-pro',
            'gemini-1.0-pro'
        ]
        self.current_model = self.models[0]  # Varsayılan model
    
    def _get_working_model(self):
        """Çalışan bir model bul"""
        if not self.client:
            return None
            
        for model in self.models:
            try:
                # Basit bir test yap
                response = self.client.models.generate_content(
                    model=model,
                    contents="test",
                    config=types.GenerateContentConfig(
                        max_output_tokens=10,
                        temperature=0.1,
                    )
                )
                if response.text:
                    logger.info(f"Working model found: {model}")
                    self.current_model = model
                    return model
            except Exception as e:
                logger.warning(f"Model {model} not working: {e}")
                continue
        
        return None
    
    def generate_response(self, message, user_context=None):
        """Tek seferlik yanıt oluştur"""
        if not self.client:
            return "❌ AI servisi şu anda kullanılamıyor. API anahtarını kontrol edin."
        
        try:
            # Çalışan model bul
            working_model = self._get_working_model()
            if not working_model:
                return "❌ Kullanılabilir AI modeli bulunamadı."
            
            system_instruction = self._get_system_instruction(user_context)
            
            response = self.client.models.generate_content(
                model=working_model,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=1000,
                    top_p=0.8,
                    top_k=40,
                )
            )
            
            if response.text:
                logger.info(f"Generated response with model: {working_model}")
                return response.text
            else:
                return "🤔 AI'dan yanıt alınamadı. Lütfen tekrar deneyin."
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"⚠️ Hata oluştu: {str(e)}"
    
    def generate_response_stream(self, message, user_context=None):
        """Stream yanıt oluştur"""
        if not self.client:
            yield "❌ AI servisi şu anda kullanılamıyor. API anahtarını kontrol edin."
            return
        
        try:
            # Çalışan model bul
            working_model = self._get_working_model()
            if not working_model:
                yield "❌ Kullanılabilir AI modeli bulunamadı."
                return
            
            system_instruction = self._get_system_instruction(user_context)
            
            logger.info(f"Starting stream with model: {working_model}")
            
            stream = self.client.models.generate_content_stream(
                model=working_model,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=1000,
                    top_p=0.8,
                    top_k=40,
                )
            )
            
            chunk_count = 0
            for chunk in stream:
                if chunk.text:
                    chunk_count += 1
                    logger.debug(f"Stream chunk {chunk_count}: {chunk.text[:20]}...")
                    yield chunk.text
            
            logger.info(f"Stream completed. Total chunks: {chunk_count}")
            
        except Exception as e:
            logger.error(f"Gemini API streaming error: {e}")
            yield f"⚠️ Stream hatası: {str(e)}"
    
    def _get_system_instruction(self, user_context):
        """Sistem talimatlarını oluştur"""
        base_instruction = """
        Sen BinaryGirls platformunun AI asistanısın. Adın Maya. 
        Türkçe konuşuyorsun ve öğrencilere ders konularında yardım ediyorsun.
        Özellikle matematik, fizik, kimya ve biyoloji konularında uzmansın.
        
        Özelliklerin:
        - Samimi ve dostane bir dil kullan
        - Açıklamaları adım adım yap
        - Örneklerle destekle
        - Motive edici ol
        - Kısa ve anlaşılır yanıtlar ver
        - Emojiler kullanarak daha canlı yaz
        """
        
        if user_context:
            user_info = f"""
            Kullanıcı bilgileri:
            - İsim: {user_context.get('name', 'Öğrenci')}
            - Seviye: {user_context.get('level', 'Genel')}
            """
            return base_instruction + user_info
        
        return base_instruction

def get_gemini_response(message, user=None):
    """Non-streaming response - Ana fonksiyon"""
    try:
        service = GeminiChatService()
        
        user_context = None
        if user and user.is_authenticated:
            user_context = {
                'name': user.get_full_name() or user.username,
                'level': getattr(user.profile, 'membership', 'basic') if hasattr(user, 'profile') else 'basic'
            }
        
        return service.generate_response(message, user_context)
    except Exception as e:
        logger.error(f"get_gemini_response error: {e}")
        return f"🚨 Sistem hatası: {str(e)}"

def get_gemini_response_stream(message, user=None):
    """Streaming response - Ana fonksiyon"""
    try:
        service = GeminiChatService()
        
        user_context = None
        if user and user.is_authenticated:
            user_context = {
                'name': user.get_full_name() or user.username,
                'level': getattr(user.profile, 'membership', 'basic') if hasattr(user, 'profile') else 'basic'
            }
        
        for chunk in service.generate_response_stream(message, user_context):
            yield chunk
    except Exception as e:
        logger.error(f"get_gemini_response_stream error: {e}")
        yield f"🚨 Sistem hatası: {str(e)}"

# Test fonksiyonu
def test_gemini_api():
    """API'yi test et"""
    try:
        response = get_gemini_response("Merhaba, nasılsın?")
        return {
            'success': True,
            'response': response,
            'client_available': GEMINI_CLIENT is not None,
            'library_available': GEMINI_AVAILABLE
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'client_available': GEMINI_CLIENT is not None,
            'library_available': GEMINI_AVAILABLE
        }