import os
import logging
from django.conf import settings
import base64
from PIL import Image
import io

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
        # Güncel modelleri dene
        self.models = [
            'gemini-2.5-flash',
            'gemini-2.5-pro',
            'gemini-1.5-flash',
            'gemini-1.5-pro'
        ]
        self.current_model = self.models[0]  # Varsayılan model
    
    def _get_working_model(self):
        """Çalışan bir model bul"""
        if not self.client:
            return None
            
        for model in self.models:
            try:
                # Basit bir test yap
                test_contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text="test")]
                    )
                ]
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=test_contents
                )
                
                if response.text:
                    logger.info(f"Working model found: {model}")
                    self.current_model = model
                    return model
            except Exception as e:
                logger.warning(f"Model {model} not working: {e}")
                continue
        
        return None
    
    def _format_chat_history(self, chat_history):
        """Chat geçmişini Gemini formatına dönüştür"""
        if not chat_history:
            return []
            
        formatted_history = []
        for message in chat_history:
            role = "model" if message.get('is_bot_response', False) else "user"
            content = message.get('message', '')
            if content.strip():
                formatted_history.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)]
                ))
        
        return formatted_history
    
    def _prepare_image_content(self, image_file):
        """Görsel dosyasını Gemini formatına hazırla"""
        try:
            # Dosyayı oku
            image_data = image_file.read()
            image_file.seek(0)  # Reset file pointer
            
            # PIL ile resmi aç ve optimize et
            img = Image.open(io.BytesIO(image_data))
            
            # Görsel boyutunu optimize et (max 2048x2048)
            max_size = 2048
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # RGB formatına dönüştür (RGBA veya P modundan kaçınmak için)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Bytes'a dönüştür
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
            img_data = img_byte_arr.getvalue()
            
            # Base64'e dönüştür
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            
            return types.Part.from_bytes(
                data=img_data,
                mime_type="image/jpeg"
            )
        except Exception as e:
            logger.error(f"Error preparing image: {e}")
            return None
    
    def _create_system_message(self, user_context):
        """Sistem mesajını oluştur"""
        base_instruction = """Sen BinaryGirls platformunun AI asistanısın. Adın Maya. 
Türkçe konuşuyorsun ve öğrencilere ders konularında yardım ediyorsun.
Özellikle matematik, fizik, kimya ve biyoloji konularında uzmansın.

Özelliklerin:
- Samimi ve dostane bir dil kullan
- Açıklamaları adım adım yap
- Örneklerle destekle
- Motive edici ol
- Kısa ve anlaşılır yanıtlar ver
- Emojiler kullanarak daha canlı yaz
- Görsel analiz etme yeteneğin var
- Chat geçmişini hatırla ve bağlam kur

Eğer görsel gönderilirse:
- Görseli detaylı şekilde analiz et
- Matematik/fen problemlerini çöz
- Grafikleri ve diyagramları açıkla
- Adım adım çözüm sun"""
        
        if user_context:
            user_info = f"""

Kullanıcı bilgileri:
- İsim: {user_context.get('name', 'Öğrenci')}
- Seviye: {user_context.get('level', 'Genel')}"""
            base_instruction += user_info
        
        return types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Sistem: {base_instruction}")]
        )
    
    def generate_response(self, message, user_context=None, chat_history=None, image_file=None):
        """Tek seferlik yanıt oluştur"""
        if not self.client:
            return "❌ AI servisi şu anda kullanılamıyor. API anahtarını kontrol edin."
        
        try:
            # Çalışan model bul
            working_model = self._get_working_model()
            if not working_model:
                return "❌ Kullanılabilir AI modeli bulunamadı."
            
            # İçerik listesini oluştur
            contents = []
            
            # Sistem mesajını ekle
            system_message = self._create_system_message(user_context)
            contents.append(system_message)
            
            # Chat geçmişini ekle
            if chat_history:
                formatted_history = self._format_chat_history(chat_history)
                contents.extend(formatted_history)
            
            # Mevcut mesajı hazırla
            message_parts = [types.Part.from_text(text=message)]
            
            # Görsel varsa ekle
            if image_file:
                image_part = self._prepare_image_content(image_file)
                if image_part:
                    message_parts.append(image_part)
            
            contents.append(types.Content(
                role="user",
                parts=message_parts
            ))
            
            # Konfigürasyon
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000,
                top_p=0.8,
                top_k=40,
                thinking_config=types.ThinkingConfig(thinking_budget=-1) if working_model.startswith('gemini-2.5') else None
            )
            
            response = self.client.models.generate_content(
                model=working_model,
                contents=contents,
                config=config
            )
            
            if response.text:
                logger.info(f"Generated response with model: {working_model}")
                return response.text
            else:
                return "🤔 AI'dan yanıt alınamadı. Lütfen tekrar deneyin."
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"⚠️ Hata oluştu: {str(e)}"
    
    def generate_response_stream(self, message, user_context=None, chat_history=None, image_file=None):
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
            
            logger.info(f"Starting stream with model: {working_model}")
            
            # İçerik listesini oluştur
            contents = []
            
            # Sistem mesajını ekle
            system_message = self._create_system_message(user_context)
            contents.append(system_message)
            
            # Chat geçmişini ekle
            if chat_history:
                formatted_history = self._format_chat_history(chat_history)
                contents.extend(formatted_history)
            
            # Mevcut mesajı hazırla
            message_parts = [types.Part.from_text(text=message)]
            
            # Görsel varsa ekle
            if image_file:
                image_part = self._prepare_image_content(image_file)
                if image_part:
                    message_parts.append(image_part)
            
            contents.append(types.Content(
                role="user",
                parts=message_parts
            ))
            
            # Konfigürasyon
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000,
                top_p=0.8,
                top_k=40,
                thinking_config=types.ThinkingConfig(thinking_budget=-1) if working_model.startswith('gemini-2.5') else None
            )
            
            chunk_count = 0
            stream = self.client.models.generate_content_stream(
                model=working_model,
                contents=contents,
                config=config
            )
            
            for chunk in stream:
                if chunk.text:
                    chunk_count += 1
                    logger.debug(f"Stream chunk {chunk_count}: {chunk.text[:20]}...")
                    yield chunk.text
            
            logger.info(f"Stream completed. Total chunks: {chunk_count}")
            
        except Exception as e:
            logger.error(f"Gemini API streaming error: {e}")
            yield f"⚠️ Stream hatası: {str(e)}"

def get_gemini_response(message, user=None, chat_history=None, image_file=None):
    """Non-streaming response - Ana fonksiyon"""
    try:
        service = GeminiChatService()
        
        user_context = None
        if user and user.is_authenticated:
            user_context = {
                'name': user.get_full_name() or user.username,
                'level': getattr(user.profile, 'membership', 'basic') if hasattr(user, 'profile') else 'basic'
            }
        
        return service.generate_response(message, user_context, chat_history, image_file)
    except Exception as e:
        logger.error(f"get_gemini_response error: {e}")
        return f"🚨 Sistem hatası: {str(e)}"

def get_gemini_response_stream(message, user=None, chat_history=None, image_file=None):
    """Streaming response - Ana fonksiyon"""
    try:
        service = GeminiChatService()
        
        user_context = None
        if user and user.is_authenticated:
            user_context = {
                'name': user.get_full_name() or user.username,
                'level': getattr(user.profile, 'membership', 'basic') if hasattr(user, 'profile') else 'basic'
            }
        
        for chunk in service.generate_response_stream(message, user_context, chat_history, image_file):
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