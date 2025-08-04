# Path: core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

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
        # Eğer başlık yoksa, ilk mesaja göre otomatik başlık oluştur
        if not self.title and self.pk:
            first_message = self.messages.filter(is_bot_response=False).first()
            if first_message:
                self.title = first_message.message[:50] + ('...' if len(first_message.message) > 50 else '')
        super().save(*args, **kwargs)
    
    def get_last_message_time(self):
        """Son mesaj zamanını döndür"""
        last_message = self.messages.last()
        return last_message.created_at if last_message else self.created_at
    
    def get_participants_preview(self):
        """Katılımcıların önizlemesini döndür"""
        messages = self.messages.all()[:3]
        preview = []
        for msg in messages:
            sender = "AI" if msg.is_bot_response else "Sen"
            preview.append(f"{sender}: {msg.message[:30]}...")
        return preview
    
    def get_short_id(self):
        """UUID'nin kısa versiyonunu döndür"""
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
    """Chat video çözümleri modeli"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='videos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_videos')
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
    
    # Video dosyası ve meta bilgiler
    video_file = models.FileField(upload_to='chat_videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='chat_video_thumbnails/', blank=True, null=True)
    actual_duration = models.DurationField(null=True, blank=True, verbose_name='Gerçek Süre')
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='Dosya Boyutu (bytes)')
    
    # İstatistikler
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    download_count = models.PositiveIntegerField(default=0, verbose_name='İndirme')
    
    # Durum
    status = models.CharField(max_length=20, choices=[
        ('generating', 'Oluşturuluyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ], default='generating')
    
    # Metadata
    chat_messages_count = models.PositiveIntegerField(default=0, verbose_name='İşlenen Mesaj Sayısı')
    generation_started_at = models.DateTimeField(auto_now_add=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Chat Videosu'
        verbose_name_plural = 'Chat Videoları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.session.user.username}"
    
    def get_short_id(self):
        """UUID'nin kısa versiyonunu döndür"""
        return str(self.id)[:8]
    
    def get_file_size_mb(self):
        """Dosya boyutunu MB cinsinden döndür"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def get_duration_display(self):
        """Süreyi okunabilir formatta döndür"""
        if self.actual_duration:
            total_seconds = int(self.actual_duration.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "0:00"
    
    def increment_view_count(self):
        """Görüntülenme sayısını artır"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        """İndirme sayısını artır"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
        

class TopicContent(models.Model):
    """Konu içerikleri modeli"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200, verbose_name='Konu Başlığı')
    description = models.TextField(verbose_name='Konu Açıklaması')
    content = models.TextField(verbose_name='Konu İçeriği')
    
    # Konu seviyesi
    LEVEL_CHOICES = [
        ('beginner', 'Başlangıç'),
        ('intermediate', 'Orta'),
        ('advanced', 'İleri'),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    
    # Konu durumu
    is_active = models.BooleanField(default=True, verbose_name='Aktif mi?')
    is_featured = models.BooleanField(default=False, verbose_name='Öne Çıkan')
    
    # Meta bilgiler
    tags = models.CharField(max_length=500, blank=True, help_text='Virgülle ayırın')
    estimated_duration = models.PositiveIntegerField(default=30, verbose_name='Tahmini Süre (dakika)')
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    
    # Tarihler
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
    
    # Dosya veya link
    file = models.FileField(upload_to='topic_materials/', blank=True, null=True)
    url = models.URLField(blank=True, verbose_name='Dış Bağlantı')
    
    # Meta bilgiler
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
    
    # Eğitim türü
    EDUCATION_TYPES = [
        ('text', 'Metin Eğitimi'),
        ('audio', 'Sesli Eğitim'),
        ('video', 'Videolu Eğitim'),
        ('interactive', 'İnteraktif Eğitim'),
    ]
    education_type = models.CharField(max_length=20, choices=EDUCATION_TYPES, default='text')
    
    # İçerik ayarları
    use_internet_search = models.BooleanField(default=False, verbose_name='İnternet Araması Kullan')
    include_materials = models.BooleanField(default=True, verbose_name='Materyalleri Dahil Et')
    
    # Eğitim tercihleri
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
    
    # Eğitim içeriği
    content = models.TextField(blank=True, verbose_name='Oluşturulan İçerik')
    
    # Ses/Video dosyaları
    audio_file = models.FileField(upload_to='education_audio/', blank=True, null=True)
    video_file = models.FileField(upload_to='education_videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='education_thumbnails/', blank=True, null=True)
    
    # Durum
    STATUS_CHOICES = [
        ('generating', 'Oluşturuluyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
    # İstatistikler
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')
    completion_rate = models.FloatField(default=0.0, verbose_name='Tamamlanma Oranı (%)')
    
    # Tarihler
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