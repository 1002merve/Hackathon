# Path: member/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os

class UserProfile(models.Model):
    MEMBERSHIP_CHOICES = [
        ('basic', 'Temel Üye'),
        ('premium', 'Premium Üye'),
        ('vip', 'VIP Üye'),
    ]
    
    GENDER_CHOICES = [
        ('female', 'Kadın'),
        ('male', 'Erkek'),
        ('other', 'Diğer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.jpg', blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='female')
    membership = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES, default='basic')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    notification_enabled = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_membership_display()}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar and hasattr(self.avatar, 'path') and os.path.exists(self.avatar.path):
            try:
                img = Image.open(self.avatar.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.avatar.path)
            except IOError:
                pass
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username
    
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/img/default-avatar.png'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Metin'),
        ('file', 'Dosya'),
        ('image', 'Resim'),
        ('audio', 'Ses'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    session = models.ForeignKey('core.ChatSession', on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file_attachment = models.FileField(upload_to='chat_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_bot_response = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']  # Chronological order within session
        verbose_name = 'Chat Mesajı'
        verbose_name_plural = 'Chat Mesajları'
    
    def __str__(self):
        session_info = f" (Oturum {self.session.id})" if self.session else ""
        return f"{self.user.username}: {self.message[:50]}...{session_info}"


class AIAvatar(models.Model):
    AVATAR_STYLES = [
        ('realistic', 'Gerçekçi'),
        ('cartoon', 'Çizgi Film'),
        ('anime', 'Anime'),
        ('3d', '3D'),
    ]
    
    HAIR_COLORS = [
        ('black', 'Siyah'),
        ('brown', 'Kahverengi'),
        ('blonde', 'Sarışın'),
        ('red', 'Kızıl'),
        ('gray', 'Gri'),
        ('other', 'Diğer'),
    ]
    
    EYE_COLORS = [
        ('brown', 'Kahverengi'),
        ('blue', 'Mavi'),
        ('green', 'Yeşil'),
        ('hazel', 'Ela'),
        ('gray', 'Gri'),
        ('amber', 'Kehribar'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_avatar')
    name = models.CharField(max_length=100, default='Maya')
    style = models.CharField(max_length=20, choices=AVATAR_STYLES, default='realistic')
    hair_color = models.CharField(max_length=20, choices=HAIR_COLORS, default='brown')
    eye_color = models.CharField(max_length=20, choices=EYE_COLORS, default='brown')
    personality = models.TextField(max_length=1000, blank=True)
    avatar_image = models.ImageField(upload_to='ai_avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'AI Avatar'
        verbose_name_plural = 'AI Avatarlar'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"