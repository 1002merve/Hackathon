# Path: core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import requests
import json
from django.conf import settings

class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name='Ders Adı')
    icon = models.CharField(max_length=10, default='📚', verbose_name='İkon')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name='Aktif mi?')
    
    class Meta:
        verbose_name = 'Ders'
        verbose_name_plural = 'Dersler'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ChatSession(models.Model):
    """Chat oturumu modeli - UUID destekli"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, blank=True, verbose_name='Oturum Başlığı')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name='Aktif Oturum')
    message_count = models.PositiveIntegerField(default=0, verbose_name='Mesaj Sayısı')
    
    class Meta:
        verbose_name = 'Chat Oturumu'
        verbose_name_plural = 'Chat Oturumları'
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.title:
            return f"{self.user.username} - {self.title}"
        return f"{self.user.username} - Oturum {str(self.id)[:8]}"
    
    def save(self, *args, **kwargs):
        if not self.title and self.pk:
            first_message = self.messages.filter(is_bot_response=False).first()
            if first_message:
                self.title = first_message.message[:50] + ('...' if len(first_message.message) > 50 else '')
        super().save(*args, **kwargs)
    
    def get_last_message_time(self):
        last_message = self.messages.last()
        return last_message.created_at if last_message else self.created_at
    
    def get_short_id(self):
        return str(self.id)[:8]


class Solution(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Kolay'),
        ('medium', 'Orta'),
        ('hard', 'Zor'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='solutions')
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(verbose_name='Açıklama')
    step_by_step = models.TextField(verbose_name='Adım Adım Çözüm')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.CharField(max_length=500, blank=True, help_text='Virgülle ayırın')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_solutions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False, verbose_name='Öne Çıkan')
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    like_count = models.PositiveIntegerField(default=0, verbose_name='Beğeni')
    
    class Meta:
        verbose_name = 'Çözüm'
        verbose_name_plural = 'Çözümler'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject.name} - {self.title}"
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class UserSolutionProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completion_time = models.DurationField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'solution']
        verbose_name = 'Kullanıcı Çözüm İlerlemesi'
        verbose_name_plural = 'Kullanıcı Çözüm İlerlemeleri'
    
    def __str__(self):
        return f"{self.user.username} - {self.solution.title}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'Mesaj'),
        ('solution', 'Çözüm'),
        ('system', 'Sistem'),
        ('achievement', 'Başarı'),
        ('video', 'Video'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bildirim'
        verbose_name_plural = 'Bildirimler'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Settings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='app_settings')
    dark_mode = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    auto_save = models.BooleanField(default=True)
    compact_view = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='tr', choices=[
        ('tr', 'Türkçe'),
        ('en', 'English'),
    ])
    
    class Meta:
        verbose_name = 'Ayar'
        verbose_name_plural = 'Ayarlar'
    
    def __str__(self):
        return f"{self.user.username} - Ayarlar"


class ChatVideo(models.Model):
    """Chat video çözümleri modeli - FastAPI entegrasyonu"""
    # Kendi ID'miz
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # FastAPI'den gelen request_id
    fastapi_request_id = models.CharField(max_length=200, unique=True, verbose_name='FastAPI Request ID')
    
    # İlişkiler
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='videos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_videos')
    
    # Video bilgileri
    title = models.CharField(max_length=200, verbose_name='Video Başlığı')
    description = models.TextField(blank=True, verbose_name='Video Açıklaması')
    
    # Video özellikleri
    video_style = models.CharField(max_length=20, choices=[
        ('animated', 'Animasyonlu'),
        ('whiteboard', 'Tahta Üzerinde'), 
        ('modern', 'Modern UI'),
    ], default='animated')
    
    duration_preference = models.CharField(max_length=10, choices=[
        ('short', 'Kısa (1-2 dakika)'),
        ('medium', 'Orta (3-5 dakika)'),
        ('long', 'Uzun (6-10 dakika)'),
    ], default='medium')
    
    speech_speed = models.CharField(max_length=10, choices=[
        ('slow', 'Yavaş'),
        ('normal', 'Normal'),
        ('fast', 'Hızlı'),
    ], default='normal')
    
    has_background_music = models.BooleanField(default=True, verbose_name='Arka Plan Müziği')
    
    # FastAPI'den gelen durumu
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Oluşturuluyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ], default='processing')
    
    # FastAPI'den gelen video URL'i
    video_url = models.URLField(blank=True, null=True, verbose_name='Video URL')
    direct_video_url = models.URLField(blank=True, null=True, verbose_name='Direkt Video URL')
    static_video_url = models.URLField(blank=True, null=True, verbose_name='Statik Video URL')
    
    # Video meta bilgileri
    file_size_mb = models.FloatField(default=0, verbose_name='Dosya Boyutu (MB)')
    actual_duration_seconds = models.PositiveIntegerField(default=0, verbose_name='Gerçek Süre (saniye)')
    
    # İstatistikler
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    download_count = models.PositiveIntegerField(default=0, verbose_name='İndirme')
    
    # Chat context
    chat_messages_json = models.TextField(verbose_name='Chat Mesajları JSON')
    message_up_to_id = models.CharField(max_length=200, verbose_name='Hangi Mesaja Kadar')
    
    # Metadata
    generation_started_at = models.DateTimeField(auto_now_add=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    last_status_check = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Chat Videosu'
        verbose_name_plural = 'Chat Videoları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.session.user.username} ({self.status})"
    
    def get_short_id(self):
        return str(self.id)[:8]
    
    def get_duration_display(self):
        if self.actual_duration_seconds:
            minutes = self.actual_duration_seconds // 60
            seconds = self.actual_duration_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "0:00"
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def update_from_fastapi_status(self, fastapi_response):
        """FastAPI'den gelen durumu güncelle"""
        if fastapi_response.get('status') == 'completed':
            self.status = 'completed'
            self.generation_completed_at = timezone.now()
            
            video_urls = fastapi_response.get('video_urls', {})
            self.video_url = video_urls.get('api')
            self.direct_video_url = video_urls.get('direct') 
            self.static_video_url = video_urls.get('static')
            
        elif fastapi_response.get('status') == 'failed':
            self.status = 'failed'
            
        self.last_status_check = timezone.now()
        self.save()
    
    @classmethod
    def create_video_request(cls, session, user, message_up_to_id, options=None):
        """FastAPI'ye video oluşturma talebi gönder ve model oluştur"""
        
        # Chat mesajlarını al
        messages = []
        message_elements = session.messages.all().order_by('created_at')
        
        for msg in message_elements:
            messages.append({
                'id': str(msg.id),
                'message': msg.message,
                'is_bot_response': msg.is_bot_response,
                'created_at': msg.created_at.isoformat()
            })
            
            if str(msg.id) == str(message_up_to_id):
                break
        
        if not options:
            options = {}
        
        # FastAPI'ye istek gönder
        try:
            # Video API URL'i settings'den al veya varsayılan kullan
            api_base = getattr(settings, 'VIDEO_API_BASE_URL', 'http://localhost:8001')
            
            payload = {
                'text': f"Sohbet oturumu: {session.get_short_id()}",
                'video_type': options.get('video_type', 'solution'),
                'chat_data': messages,
                'options': {
                    'style': options.get('style', 'animated'),
                    'duration': options.get('duration', 'medium'),
                    'speed': options.get('speed', 'normal'),
                    'background_music': options.get('background_music', True)
                }
            }
            
            response = requests.post(
                f"{api_base}/api/create_video",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                fastapi_data = response.json()
                
                # Django modelini oluştur
                video = cls.objects.create(
                    fastapi_request_id=fastapi_data.get('request_id'),
                    session=session,
                    user=user,
                    title=f"Video Çözüm - {session.title or session.get_short_id()}",
                    description=f"Sohbet {session.get_short_id()} için AI destekli video çözümü",
                    video_style=options.get('style', 'animated'),
                    duration_preference=options.get('duration', 'medium'),
                    speech_speed=options.get('speed', 'normal'),
                    has_background_music=options.get('background_music', True),
                    chat_messages_json=json.dumps(messages),
                    message_up_to_id=str(message_up_to_id),
                    status='processing'
                )
                
                return video, fastapi_data
                
            else:
                raise Exception(f"FastAPI error: {response.status_code} - {response.text}")
                
        except Exception as e:
            # Hata durumunda bile model oluştur
            video = cls.objects.create(
                fastapi_request_id=f"error_{uuid.uuid4()}",
                session=session,
                user=user,
                title=f"Video Çözüm - {session.title or session.get_short_id()} (Hata)",
                description=f"Video oluşturma hatası: {str(e)}",
                video_style=options.get('style', 'animated'),
                duration_preference=options.get('duration', 'medium'),
                speech_speed=options.get('speed', 'normal'),
                has_background_music=options.get('background_music', True),
                chat_messages_json=json.dumps(messages),
                message_up_to_id=str(message_up_to_id),
                status='failed'
            )
            
            return video, {'error': str(e)}
    
    def check_fastapi_status(self):
        """FastAPI'den video durumunu kontrol et"""
        if self.status == 'completed' or self.status == 'failed':
            return
            
        try:
            api_base = getattr(settings, 'VIDEO_API_BASE_URL', 'http://localhost:8001')
            response = requests.get(
                f"{api_base}/api/status/{self.fastapi_request_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.update_from_fastapi_status(data)
                
        except Exception as e:
            print(f"FastAPI status check error: {e}")


class TopicContent(models.Model):
    """Konu içerikleri modeli"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200, verbose_name='Konu Başlığı')
    description = models.TextField(verbose_name='Konu Açıklaması')
    content = models.TextField(verbose_name='Konu İçeriği')
    
    LEVEL_CHOICES = [
        ('beginner', 'Başlangıç'),
        ('intermediate', 'Orta'),
        ('advanced', 'İleri'),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    
    is_active = models.BooleanField(default=True, verbose_name='Aktif mi?')
    is_featured = models.BooleanField(default=False, verbose_name='Öne Çıkan')
    
    tags = models.CharField(max_length=500, blank=True, help_text='Virgülle ayırın')
    estimated_duration = models.PositiveIntegerField(default=30, verbose_name='Tahmini Süre (dakika)')
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_topics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Konu İçeriği'
        verbose_name_plural = 'Konu İçerikleri'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject.name} - {self.title}"
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class TopicMaterial(models.Model):
    """Konu materyalleri (PDF, dökümanlar vb.)"""
    topic = models.ForeignKey(TopicContent, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200, verbose_name='Materyal Başlığı')
    
    MATERIAL_TYPES = [
        ('pdf', 'PDF Doküman'),
        ('doc', 'Word Doküman'),
        ('video', 'Video'),
        ('audio', 'Ses Dosyası'),
        ('image', 'Görsel'),
        ('link', 'Dış Bağlantı'),
    ]
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='pdf')
    
    file = models.FileField(upload_to='topic_materials/', blank=True, null=True)
    url = models.URLField(blank=True, verbose_name='Dış Bağlantı')
    
    description = models.TextField(blank=True, verbose_name='Açıklama')
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='Dosya Boyutu (bytes)')
    download_count = models.PositiveIntegerField(default=0, verbose_name='İndirme Sayısı')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Konu Materyali'
        verbose_name_plural = 'Konu Materyalleri'
        ordering = ['material_type', 'title']
    
    def __str__(self):
        return f"{self.topic.title} - {self.title}"
    
    def get_file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0


class EducationSession(models.Model):
    """AI ile oluşturulan eğitim oturumları"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education_sessions')
    topic = models.ForeignKey(TopicContent, on_delete=models.CASCADE, related_name='education_sessions')
    
    title = models.CharField(max_length=200, verbose_name='Eğitim Başlığı')
    description = models.TextField(blank=True, verbose_name='Eğitim Açıklaması')
    
    EDUCATION_TYPES = [
        ('text', 'Metin Eğitimi'),
        ('audio', 'Sesli Eğitim'),
        ('video', 'Videolu Eğitim'),
        ('interactive', 'İnteraktif Eğitim'),
    ]
    education_type = models.CharField(max_length=20, choices=EDUCATION_TYPES, default='text')
    
    use_internet_search = models.BooleanField(default=False, verbose_name='İnternet Araması Kullan')
    include_materials = models.BooleanField(default=True, verbose_name='Materyalleri Dahil Et')
    
    language = models.CharField(max_length=10, default='tr', choices=[
        ('tr', 'Türkçe'),
        ('en', 'English'),
    ])
    
    difficulty_level = models.CharField(max_length=20, choices=[
        ('easy', 'Kolay'),
        ('medium', 'Orta'),
        ('hard', 'Zor'),
    ], default='medium')
    
    estimated_duration = models.PositiveIntegerField(default=30, verbose_name='Tahmini Süre (dakika)')
    content = models.TextField(blank=True, verbose_name='Oluşturulan İçerik')
    
    audio_file = models.FileField(upload_to='education_audio/', blank=True, null=True)
    video_file = models.FileField(upload_to='education_videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='education_thumbnails/', blank=True, null=True)
    
    STATUS_CHOICES = [
        ('generating', 'Oluşturuluyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    completion_rate = models.FloatField(default=0.0, verbose_name='Tamamlanma Oranı (%)')
    
    generation_started_at = models.DateTimeField(auto_now_add=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Eğitim Oturumu'
        verbose_name_plural = 'Eğitim Oturumları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_short_id(self):
        return str(self.id)[:8]
    
    def get_duration_display(self):
        if self.estimated_duration:
            hours = self.estimated_duration // 60
            minutes = self.estimated_duration % 60
            if hours > 0:
                return f"{hours}s {minutes}dk"
            return f"{minutes}dk"
        return "Bilinmiyor"
    
    def increment_view_count(self):
        self.view_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_accessed_at'])