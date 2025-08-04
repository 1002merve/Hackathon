# Path: member/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, ChatMessage, AIAvatar

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil Bilgileri'
    fields = (
        'avatar', 'phone', 'bio', 'birth_date', 'gender', 
        'membership', 'is_verified', 'notification_enabled', 'dark_mode'
    )

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_membership')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__membership', 'profile__gender')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_membership(self, obj):
        return obj.profile.get_membership_display()
    get_membership.short_description = 'Üyelik'

# Yeniden kaydet
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership', 'gender', 'is_verified', 'created_at')
    list_filter = ('membership', 'gender', 'is_verified', 'notification_enabled', 'dark_mode')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user', 'avatar')
        }),
        ('Kişisel Bilgiler', {
            'fields': ('phone', 'bio', 'birth_date', 'gender')
        }),
        ('Üyelik Bilgileri', {
            'fields': ('membership', 'is_verified')
        }),
        ('Ayarlar', {
            'fields': ('notification_enabled', 'dark_mode')
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'message_type', 'is_bot_response', 'created_at')
    list_filter = ('message_type', 'is_bot_response', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mesaj Önizleme'

@admin.register(AIAvatar)
class AIAvatarAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'style', 'hair_color', 'eye_color', 'is_active', 'created_at')
    list_filter = ('style', 'hair_color', 'eye_color', 'is_active')
    search_fields = ('user__username', 'name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Avatar Bilgileri', {
            'fields': ('user', 'name', 'avatar_image', 'is_active')
        }),
        ('Görünüm Ayarları', {
            'fields': ('style', 'hair_color', 'eye_color')
        }),
        ('Kişilik', {
            'fields': ('personality',)
        }),
        ('Tarih', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )