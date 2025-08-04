from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Settings, Notification


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Yeni kullanıcı için varsayılan ayarları oluştur"""
    if created:
        Settings.objects.create(user=instance)
        
        # Hoş geldin bildirimi oluştur
        Notification.objects.create(
            user=instance,
            title='BinaryGirls\'e Hoş Geldiniz! 🎉',
            message='Hesabınız başarıyla oluşturuldu. AI asistanınızla sohbet etmeye başlayabilirsiniz!',
            notification_type='system'
        )