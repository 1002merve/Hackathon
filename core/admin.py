# Path: core/admin.py

from django.contrib import admin
from .models import Subject, Solution, UserSolutionProgress, Notification, Settings, ChatSession

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'solution_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    def solution_count(self, obj):
        return obj.solutions.count()
    solution_count.short_description = 'Çözüm Sayısı'


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'message_count', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('user__username', 'title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Oturum Bilgileri', {
            'fields': ('user', 'title', 'is_active')
        }),
        ('İstatistikler', {
            'fields': ('message_count',)
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'difficulty', 'created_by', 'view_count', 'like_count', 'is_featured', 'created_at')
    list_filter = ('subject', 'difficulty', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('view_count', 'like_count', 'created_at', 'updated_at')
    filter_horizontal = ()
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'subject', 'difficulty', 'is_featured')
        }),
        ('İçerik', {
            'fields': ('description', 'step_by_step', 'tags')
        }),
        ('Meta Bilgiler', {
            'fields': ('created_by', 'view_count', 'like_count')
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSolutionProgress)
class UserSolutionProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'solution', 'is_completed', 'rating', 'completion_time', 'completed_at')
    list_filter = ('is_completed', 'rating', 'solution__subject', 'solution__difficulty')
    search_fields = ('user__username', 'solution__title')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Kullanıcı ve Çözüm', {
            'fields': ('user', 'solution')
        }),
        ('İlerleme Durumu', {
            'fields': ('is_completed', 'completion_time', 'completed_at')
        }),
        ('Değerlendirme', {
            'fields': ('rating', 'notes')
        }),
        ('Tarih', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Bildirim Bilgileri', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Durum', {
            'fields': ('is_read',)
        }),
        ('Tarih', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} bildirim okundu olarak işaretlendi.')
    mark_as_read.short_description = 'Seçili bildirimleri okundu olarak işaretle'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} bildirim okunmadı olarak işaretlendi.')
    mark_as_unread.short_description = 'Seçili bildirimleri okunmadı olarak işaretle'


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode', 'notifications_enabled', 'language')
    list_filter = ('dark_mode', 'notifications_enabled', 'language', 'auto_save')
    search_fields = ('user__username',)
    
    fieldsets = (
        ('Kullanıcı', {
            'fields': ('user',)
        }),
        ('Görünüm Ayarları', {
            'fields': ('dark_mode', 'compact_view', 'language')
        }),
        ('Bildirim Ayarları', {
            'fields': ('notifications_enabled', 'email_notifications', 'sound_enabled')
        }),
        ('Uygulama Ayarları', {
            'fields': ('auto_save',)
        }),
    )