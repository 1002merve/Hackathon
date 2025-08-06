from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404, StreamingHttpResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import logging
import time
from datetime import datetime, timedelta

from .models import Subject, Solution, UserSolutionProgress, Notification, Settings, ChatSession, ChatVideo,TopicContent,EducationSession
from member.models import ChatMessage
from .utils import get_gemini_response, get_gemini_response_stream

logger = logging.getLogger(__name__)




@login_required
def chat_stream_response(request):
    """AI chat streaming response - YENİ API VERSIYONU"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        session_id = data.get('session_id', '')
        has_image = data.get('has_image', False)
        
        logger.info(f"Stream request - Message: {message_text[:50]}... Session: {session_id} Has Image: {has_image}")
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Message is required'})
        
        if not session_id:
            return JsonResponse({'success': False, 'error': 'Session ID is required'})
        
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            logger.error(f"Session not found: {session_id}")
            return JsonResponse({'success': False, 'error': 'Session not found'})
        
        # Chat geçmişini al (son 20 mesaj)
        chat_history = ChatMessage.objects.filter(
            user=request.user,
            session=session
        ).order_by('created_at')[:20]
        
        # Geçmişi uygun formata dönüştür (yeni API için)
        formatted_history = []
        for msg in chat_history:
            formatted_history.append({
                'message': msg.message,
                'is_bot_response': msg.is_bot_response,
                'created_at': msg.created_at.isoformat()
            })
        
        # Görsel dosyası varsa al
        image_file = None
        if has_image:
            # Session'daki en son user mesajından dosyayı bul
            last_user_message = ChatMessage.objects.filter(
                user=request.user,
                session=session,
                is_bot_response=False,
                file_attachment__isnull=False
            ).order_by('-created_at').first()
            
            if last_user_message and last_user_message.file_attachment:
                image_file = last_user_message.file_attachment
        
        def generate_stream():
            """Stream generator function"""
            try:
                logger.info("Starting stream generation with history")
                
                # Bot mesajını oluştur
                bot_message = ChatMessage.objects.create(
                    user=request.user,
                    session=session,
                    message="",
                    is_bot_response=True
                )
                
                full_response = ""
                chunk_count = 0
                
                try:
                    logger.info(f"Calling Gemini API with {len(formatted_history)} history messages")
                    
                    # Gemini API'den stream al - geçmiş ve görsel ile birlikte
                    for chunk in get_gemini_response_stream(
                        message_text, 
                        request.user, 
                        chat_history=formatted_history,
                        image_file=image_file
                    ):
                        if chunk:
                            chunk_count += 1
                            full_response += chunk
                            
                            chunk_data = {
                                'chunk': chunk,
                                'message_id': bot_message.id,
                                'timestamp': datetime.now().strftime('%H:%M')
                            }
                            
                            # SSE formatında gönder
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                            logger.debug(f"Sent chunk {chunk_count}: {chunk[:20]}...")
                    
                    # Final mesajı kaydet
                    bot_message.message = full_response if full_response else "Yanıt oluşturulamadı."
                    bot_message.save()
                    
                    # Session'ı güncelle
                    session.updated_at = timezone.now()
                    session.save()
                    
                    # Tamamlandı sinyali gönder
                    final_data = {
                        'done': True,
                        'message_id': bot_message.id,
                        'full_message': bot_message.message
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                    logger.info(f"Stream completed. Total chunks: {chunk_count}")
                    
                except Exception as stream_error:
                    logger.error(f"Stream generation error: {str(stream_error)}")
                    error_message = f"Yanıt oluştururken hata: {str(stream_error)}"
                    
                    bot_message.message = error_message
                    bot_message.save()
                    
                    error_data = {
                        'error': True,
                        'message': error_message,
                        'message_id': bot_message.id
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    
            except Exception as e:
                logger.error(f"Stream function error: {str(e)}")
                error_response = {
                    'error': True, 
                    'message': f'Sistem hatası: {str(e)}'
                }
                yield f"data: {json.dumps(error_response)}\n\n"
        
        # StreamingHttpResponse oluştur
        response = StreamingHttpResponse(
            generate_stream(),
            content_type='text/plain; charset=utf-8'
        )
        
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        
        logger.info("Stream response created successfully")
        return response
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Chat stream error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Internal server error: {str(e)}'})


@login_required
def chat_view(request):
    """Ana chat view fonksiyonu - YENİ API VERSIYONU"""
    active_session = ChatSession.objects.filter(user=request.user, is_active=True).first()
    
    if not active_session:
        active_session = ChatSession.objects.create(user=request.user, is_active=True)
    
    messages_list = ChatMessage.objects.filter(
        user=request.user, 
        session=active_session
    ).order_by('created_at')
    
    session_videos = ChatVideo.objects.filter(
        session=active_session
    ).order_by('-created_at')
    
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            data = json.loads(request.body)
            message_text = data.get('message', '').strip()
            action = data.get('action', 'send_message')
            
            logger.info(f"Chat POST request - Action: {action}, Message: {message_text[:30]}...")
            
            if action == 'new_chat':
                # Mevcut session'ı kapat
                if active_session.messages.exists():
                    active_session.is_active = False
                    active_session.message_count = active_session.messages.count()
                    active_session.save()
                    
                    # Başlık oluştur
                    if not active_session.title:
                        first_message = active_session.messages.filter(is_bot_response=False).first()
                        if first_message:
                            active_session.title = first_message.message[:50] + ('...' if len(first_message.message) > 50 else '')
                            active_session.save()
                
                # Yeni session oluştur
                active_session = ChatSession.objects.create(user=request.user, is_active=True)
                
                return JsonResponse({
                    'success': True,
                    'action': 'new_chat',
                    'session_id': str(active_session.id),
                    'message': 'Yeni sohbet başlatıldı!'
                })
            
            elif action == 'send_message' and message_text:
                # User mesajını kaydet
                user_message = ChatMessage.objects.create(
                    user=request.user,
                    session=active_session,
                    message=message_text,
                    is_bot_response=False
                )
                
                # Session'ı güncelle
                active_session.updated_at = timezone.now()
                active_session.save()
                
                return JsonResponse({
                    'success': True,
                    'action': 'send_message',
                    'user_message': {
                        'id': user_message.id,
                        'message': user_message.message,
                        'timestamp': user_message.created_at.strftime('%H:%M'),
                        'sender': 'user'
                    },
                    'session_id': str(active_session.id)
                })
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action or empty message'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            logger.error(f"Chat view error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    elif request.method == 'POST':
        # Form data ile gelen dosya yükleme işlemi
        message_text = request.POST.get('message', '').strip()
        uploaded_file = request.FILES.get('file')
        
        if message_text or uploaded_file:
            # Dosya tipini kontrol et
            message_type = 'text'
            if uploaded_file:
                if uploaded_file.content_type.startswith('image/'):
                    message_type = 'image'
                elif uploaded_file.content_type.startswith('audio/'):
                    message_type = 'audio'
                else:
                    message_type = 'file'
            
            user_message = ChatMessage.objects.create(
                user=request.user,
                session=active_session,
                message=message_text if message_text else "📷 Görsel yüklendi",
                is_bot_response=False,
                file_attachment=uploaded_file if uploaded_file else None,
                message_type=message_type
            )
            
            # Session'ı güncelle
            active_session.updated_at = timezone.now()
            active_session.save()
            
            # AJAX request ise JSON döndür
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response_data = {
                    'success': True,
                    'action': 'send_message',
                    'user_message': {
                        'id': user_message.id,
                        'message': user_message.message,
                        'timestamp': user_message.created_at.strftime('%H:%M'),
                        'sender': 'user',
                        'has_file': bool(uploaded_file),
                        'file_url': user_message.file_attachment.url if user_message.file_attachment else None,
                        'file_type': message_type
                    },
                    'session_id': str(active_session.id)
                }
                return JsonResponse(response_data)
            
            # Normal form post ise redirect
            return redirect('core:chat')
    
    context = {
        'messages': messages_list,
        'active_session': active_session,
        'session_id': str(active_session.id),
        'session_videos': session_videos,
        'title': 'Soru Çöz'
    }
    
    return render(request, 'core/chat.html', context)

  
# Dashboard view'u değişmedi, aynı kalabilir
@login_required
def dashboard(request):
    total_solutions = Solution.objects.count()
    user_completed = UserSolutionProgress.objects.filter(
        user=request.user, 
        is_completed=True
    ).count()
    user_messages = ChatMessage.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).count()
    
    recent_solutions = Solution.objects.filter(is_featured=True)[:6]
    
    recent_progress = UserSolutionProgress.objects.filter(
        user=request.user
    ).select_related('solution').order_by('-created_at')[:5]
    
    total_chat_sessions = ChatSession.objects.filter(user=request.user).count()
    
    context = {
        'total_solutions': total_solutions,
        'user_completed': user_completed,
        'user_messages': user_messages,
        'total_chat_sessions': total_chat_sessions,
        'unread_notifications': unread_notifications,
        'recent_solutions': recent_solutions,
        'recent_progress': recent_progress,
        'completion_percentage': (user_completed / total_solutions * 100) if total_solutions > 0 else 0,
        'title': 'Kontrol Paneli'
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def chat_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user).annotate(
        message_count_actual=Count('messages')
    ).order_by('-updated_at')
    
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sessions': page_obj,
        'title': 'Sohbet Oturumları'
    }
    
    return render(request, 'core/chat_sessions.html', context)


@login_required
def chat_session_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = ChatMessage.objects.filter(session=session).order_by('created_at')
    videos = ChatVideo.objects.filter(session=session).order_by('-created_at')
    
    context = {
        'session': session,
        'messages': messages,
        'videos': videos,
        'title': f'Oturum: {session.title or f"Oturum {session.get_short_id()}"}'
    }
    
    return render(request, 'core/chat_session_detail.html', context)


@login_required
def load_chat_session(request, session_id):
    if request.method == 'POST':
        ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.is_active = True
        session.save()
        
        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'redirect_url': '/core/chat/'
        })
    
    return JsonResponse({'success': False})


@login_required
def continue_chat_session(request, session_id):
    if request.method == 'POST':
        ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.is_active = True
        session.save()
        
        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'redirect_url': '/core/chat/',
            'message': f'"{session.title or "Oturum"}" devam ettiriliyor...'
        })
    
    return JsonResponse({'success': False})


@login_required
def delete_chat_session(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        if session.is_active:
            ChatSession.objects.create(user=request.user, is_active=True)
        
        session.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Oturum silindi'
        })
    
    return JsonResponse({'success': False})


@login_required
def generate_chat_video(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            message_id = data.get('message_id')
            video_options = data.get('video_options', {})
            
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            
            title = f"Video Çözüm - {session.title or session.get_short_id()}"
            
            video = ChatVideo.objects.create(
                session=session,
                user=request.user,
                title=title,
                description=f"Oturum {session.get_short_id()} için video çözümü",
                video_style=video_options.get('style', 'animated'),
                duration_preference=video_options.get('duration', 'medium'),
                speech_speed=video_options.get('speed', 'normal'),
                has_background_music=video_options.get('background_music', True),
                chat_messages_count=session.messages.count(),
                status='generating'
            )
            
            import threading
            import time
            
            def simulate_video_generation():
                time.sleep(3)
                video.status = 'completed'
                video.generation_completed_at = timezone.now()
                video.actual_duration = timedelta(minutes=4, seconds=32)
                video.file_size = 15728640
                video.save()
            
            thread = threading.Thread(target=simulate_video_generation)
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                'success': True,
                'video_id': str(video.id),
                'message': 'Video oluşturma başlatıldı!',
                'estimated_time': '30-60 saniye'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def chat_video_detail(request, video_id):
    video = get_object_or_404(ChatVideo, id=video_id, user=request.user)
    video.increment_view_count()
    
    return JsonResponse({
        'success': True,
        'video': {
            'id': str(video.id),
            'title': video.title,
            'status': video.status,
            'duration': video.get_duration_display(),
            'file_size': video.get_file_size_mb(),
            'view_count': video.view_count,
            'download_count': video.download_count,
            'created_at': video.created_at.isoformat()
        }
    })


@login_required
def download_chat_video(request, video_id):
    video = get_object_or_404(ChatVideo, id=video_id, user=request.user)
    
    if video.status != 'completed' or not video.video_file:
        return JsonResponse({'success': False, 'error': 'Video henüz hazır değil'})
    
    video.increment_download_count()
    
    return JsonResponse({
        'success': True,
        'download_url': video.video_file.url if video.video_file else None,
        'filename': f"binarygirls_video_{video.get_short_id()}.mp4"
    })


@login_required 
def get_chat_sessions_api(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:10]
    
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            'id': str(session.id),
            'title': session.title or f'Oturum {session.get_short_id()}',
            'is_active': session.is_active,
            'message_count': session.messages.count(),
            'created_at': session.created_at.strftime('%d.%m.%Y %H:%M'),
            'updated_at': session.updated_at.strftime('%d.%m.%Y %H:%M'),
            'last_message_time': session.get_last_message_time().strftime('%d.%m.%Y %H:%M')
        })
    
    return JsonResponse({
        'success': True,
        'sessions': sessions_data
    })


@login_required
def chat_history(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_sessions = sessions.count()
    total_messages = ChatMessage.objects.filter(user=request.user).count()
    user_messages = ChatMessage.objects.filter(user=request.user, is_bot_response=False).count()
    bot_messages = ChatMessage.objects.filter(user=request.user, is_bot_response=True).count()
    total_videos = ChatVideo.objects.filter(user=request.user).count()
    
    context = {
        'sessions': page_obj,
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'user_messages': user_messages,
        'bot_messages': bot_messages,
        'total_videos': total_videos,
        'title': 'Chat Geçmişi'
    }
    
    return render(request, 'core/chat_history.html', context)


@login_required
def export_chat_history(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    export_data = {
        'user': request.user.username,
        'export_date': datetime.now().isoformat(),
        'total_sessions': sessions.count(),
        'sessions': []
    }
    
    for session in sessions:
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        videos = ChatVideo.objects.filter(session=session).order_by('created_at')
        
        session_data = {
            'session_id': str(session.id),
            'title': session.title or f'Oturum {session.get_short_id()}',
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': messages.count(),
            'video_count': videos.count(),
            'messages': [],
            'videos': []
        }
        
        for message in messages:
            session_data['messages'].append({
                'id': message.id,
                'message': message.message,
                'is_bot_response': message.is_bot_response,
                'created_at': message.created_at.isoformat(),
                'sender': 'AI Assistant' if message.is_bot_response else f'{request.user.get_full_name() or request.user.username}'
            })
        
        for video in videos:
            session_data['videos'].append({
                'id': str(video.id),
                'title': video.title,
                'status': video.status,
                'duration': video.get_duration_display(),
                'file_size_mb': video.get_file_size_mb(),
                'created_at': video.created_at.isoformat()
            })
        
        export_data['sessions'].append(session_data)
    
    response = JsonResponse(export_data)
    response['Content-Disposition'] = f'attachment; filename="binarygirls_chat_history_{request.user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response


@login_required
def solutions_list(request, subject_id=None):
    solutions = Solution.objects.all().select_related('subject', 'created_by')
    subjects = Subject.objects.filter(is_active=True).annotate(
        solution_count=Count('solutions')
    )
    
    if subject_id:
        subject = get_object_or_404(Subject, id=subject_id)
        solutions = solutions.filter(subject=subject)
    
    search_query = request.GET.get('search')
    if search_query:
        solutions = solutions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    difficulty = request.GET.get('difficulty')
    if difficulty:
        solutions = solutions.filter(difficulty=difficulty)
    
    paginator = Paginator(solutions, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    user_chat_stats = {
        'total_messages': ChatMessage.objects.filter(user=request.user).count(),
        'recent_topics': get_recent_chat_topics(request.user)
    }
    
    context = {
        'solutions': page_obj,
        'subjects': subjects,
        'current_subject': subject_id,
        'search_query': search_query,
        'current_difficulty': difficulty,
        'user_chat_stats': user_chat_stats,
        'title': 'Çözümler'
    }
    
    return render(request, 'core/solutions_list.html', context)


def get_recent_chat_topics(user):
    recent_messages = ChatMessage.objects.filter(
        user=user, 
        is_bot_response=False
    ).order_by('-created_at')[:10]
    
    topics = []
    for message in recent_messages:
        message_lower = message.message.lower()
        if any(keyword in message_lower for keyword in ['matematik', 'mat', 'sayı']):
            topics.append('Matematik')
        elif any(keyword in message_lower for keyword in ['fizik', 'hareket', 'kuvvet']):
            topics.append('Fizik')
        elif any(keyword in message_lower for keyword in ['kimya', 'atom', 'molekül']):
            topics.append('Kimya')
        elif any(keyword in message_lower for keyword in ['biyoloji', 'bio', 'hücre']):
            topics.append('Biyoloji')
    
    from collections import Counter
    topic_counts = Counter(topics)
    return [topic for topic, count in topic_counts.most_common(3)]


@login_required
def solution_detail(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)
    
    solution.view_count += 1
    solution.save(update_fields=['view_count'])
    
    progress, created = UserSolutionProgress.objects.get_or_create(
        user=request.user,
        solution=solution
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            progress.is_completed = True
            progress.save()
            messages.success(request, 'Çözüm tamamlandı olarak işaretlendi!')
            
        elif action == 'rate':
            rating = request.POST.get('rating')
            if rating:
                progress.rating = int(rating)
                progress.save()
                messages.success(request, 'Değerlendirmeniz kaydedildi!')
    
    similar_solutions = Solution.objects.filter(
        subject=solution.subject
    ).exclude(id=solution.id)[:3]
    
    related_chat_messages = get_related_chat_messages(request.user, solution.subject.name)
    
    context = {
        'solution': solution,
        'progress': progress,
        'similar_solutions': similar_solutions,
        'related_chat_messages': related_chat_messages,
        'title': solution.title
    }
    
    return render(request, 'core/solution_detail.html', context)


def get_related_chat_messages(user, subject_name):
    keywords = {
        'Matematik': ['matematik', 'mat', 'sayı', 'hesap', 'algebra', 'geometri'],
        'Fizik': ['fizik', 'hareket', 'kuvvet', 'enerji'],
        'Kimya': ['kimya', 'atom', 'molekül', 'element'],
        'Biyoloji': ['biyoloji', 'bio', 'hücre', 'dna']
    }
    
    subject_keywords = keywords.get(subject_name, [])
    if not subject_keywords:
        return []
    
    messages = ChatMessage.objects.filter(user=user)
    related_messages = []
    
    for message in messages:
        if any(keyword in message.message.lower() for keyword in subject_keywords):
            related_messages.append(message)
    
    return related_messages[:5]


@login_required
def settings_view(request):
    settings, created = Settings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        settings.dark_mode = request.POST.get('dark_mode') == 'on'
        settings.notifications_enabled = request.POST.get('notifications_enabled') == 'on'
        settings.email_notifications = request.POST.get('email_notifications') == 'on'
        settings.sound_enabled = request.POST.get('sound_enabled') == 'on'
        settings.auto_save = request.POST.get('auto_save') == 'on'
        settings.compact_view = request.POST.get('compact_view') == 'on'
        settings.language = request.POST.get('language', 'tr')
        settings.save()
        
        messages.success(request, 'Ayarlarınız başarıyla kaydedildi!')
        return redirect('core:settings')
    
    context = {
        'settings': settings,
        'title': 'Ayarlar'
    }
    
    return render(request, 'core/settings.html', context)


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'title': 'Bildirimler'
    }
    
    return render(request, 'core/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
def get_user_stats(request):
    stats = {
        'total_solutions': Solution.objects.count(),
        'completed_solutions': UserSolutionProgress.objects.filter(
            user=request.user, 
            is_completed=True
        ).count(),
        'total_messages': ChatMessage.objects.filter(user=request.user).count(),
        'chat_sessions': get_chat_sessions_count(request.user),
        'total_videos': ChatVideo.objects.filter(user=request.user).count(),
        'subjects_progress': {},
        'recent_activity': get_recent_activity(request.user)
    }
    
    subjects = Subject.objects.filter(is_active=True)
    for subject in subjects:
        total = Solution.objects.filter(subject=subject).count()
        completed = UserSolutionProgress.objects.filter(
            user=request.user,
            solution__subject=subject,
            is_completed=True
        ).count()
        
        stats['subjects_progress'][subject.name] = {
            'total': total,
            'completed': completed,
            'percentage': (completed / total * 100) if total > 0 else 0,
            'chat_messages': ChatMessage.objects.filter(
                user=request.user,
                message__icontains=subject.name.lower()
            ).count()
        }
    
    return JsonResponse(stats)


def get_chat_sessions_count(user):
    return ChatSession.objects.filter(user=user).count()


def get_recent_activity(user):
    activities = []
    
    recent_chats = ChatMessage.objects.filter(
        user=user, 
        is_bot_response=False
    ).order_by('-created_at')[:3]
    
    for chat in recent_chats:
        activities.append({
            'type': 'chat',
            'description': f'Chat: {chat.message[:50]}...',
            'timestamp': chat.created_at.isoformat()
        })
    
    recent_completions = UserSolutionProgress.objects.filter(
        user=user,
        is_completed=True
    ).order_by('-completed_at')[:3]
    
    for completion in recent_completions:
        activities.append({
            'type': 'completion',
            'description': f'Çözüm tamamlandı: {completion.solution.title}',
            'timestamp': completion.completed_at.isoformat() if completion.completed_at else completion.created_at.isoformat()
        })
    
    recent_videos = ChatVideo.objects.filter(
        user=user,
        status='completed'
    ).order_by('-created_at')[:2]
    
    for video in recent_videos:
        activities.append({
            'type': 'video',
            'description': f'Video oluşturuldu: {video.title}',
            'timestamp': video.created_at.isoformat()
        })
    
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:5]


def home(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    total_users = ChatMessage.objects.values('user').distinct().count()
    total_solutions = Solution.objects.count()
    featured_solutions = Solution.objects.filter(is_featured=True)[:3]
    
    context = {
        'total_users': total_users,
        'total_solutions': total_solutions,
        'featured_solutions': featured_solutions,
        'title': 'BinaryGirls - AI Destekli Asistan'
    }
    
    return render(request, 'core/home.html', context)



@login_required
def topic_tutorial(request):
    """Ana konu anlatım sayfası"""
    subjects = Subject.objects.filter(is_active=True).annotate(
        topic_count=Count('topics')
    )
    
    featured_topics = TopicContent.objects.filter(
        is_active=True, 
        is_featured=True
    ).select_related('subject', 'created_by')[:6]
    
    recent_topics = TopicContent.objects.filter(
        is_active=True
    ).select_related('subject', 'created_by').order_by('-created_at')[:8]
    
    # Kullanıcının son eğitimleri
    user_recent_sessions = EducationSession.objects.filter(
        user=request.user
    ).select_related('topic').order_by('-created_at')[:5]
    
    context = {
        'subjects': subjects,
        'featured_topics': featured_topics,
        'recent_topics': recent_topics,
        'user_recent_sessions': user_recent_sessions,
        'title': 'Konu Anlatım'
    }
    
    return render(request, 'core/topic_tutorial.html', context)


@login_required
def topic_detail(request, topic_id):
    """Konu detay sayfası"""
    topic = get_object_or_404(TopicContent, id=topic_id, is_active=True)
    
    # Görüntülenme sayısını artır
    topic.view_count += 1
    topic.save(update_fields=['view_count'])
    
    materials = topic.materials.all().order_by('material_type', 'title')
    
    # Kullanıcının bu konudaki eğitim oturumları
    user_sessions = EducationSession.objects.filter(
        user=request.user,
        topic=topic
    ).order_by('-created_at')
    
    # Benzer konular
    similar_topics = TopicContent.objects.filter(
        subject=topic.subject,
        is_active=True
    ).exclude(id=topic.id)[:4]
    
    context = {
        'topic': topic,
        'materials': materials,
        'user_sessions': user_sessions,
        'similar_topics': similar_topics,
        'title': topic.title
    }
    
    return render(request, 'core/topic_detail.html', context)


@login_required
def create_education(request):
    """Eğitim oluşturma sayfası"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic_id = data.get('topic_id')
            education_type = data.get('education_type', 'text')
            options = data.get('options', {})
            
            topic = get_object_or_404(TopicContent, id=topic_id, is_active=True)
            
            # Yeni eğitim oturumu oluştur
            session = EducationSession.objects.create(
                user=request.user,
                topic=topic,
                title=f"{education_type.title()} - {topic.title}",
                education_type=education_type,
                use_internet_search=options.get('use_internet_search', False),
                include_materials=options.get('include_materials', True),
                language=options.get('language', 'tr'),
                difficulty_level=options.get('difficulty_level', 'medium'),
                estimated_duration=options.get('duration', 30)
            )
            
            # Arka planda eğitim içeriği oluştur
            import threading
            
            def generate_education_content():
                try:
                    # AI ile içerik oluşturma simülasyonu
                    import time
                    time.sleep(5)
                    
                    content = generate_education_content_with_ai(session)
                    
                    session.content = content
                    session.status = 'completed'
                    session.generation_completed_at = timezone.now()
                    session.save()
                    
                except Exception as e:
                    session.status = 'failed'
                    session.save()
            
            thread = threading.Thread(target=generate_education_content)
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                'success': True,
                'session_id': str(session.id),
                'message': f'{education_type.title()} eğitimi oluşturuluyor...'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # GET request için konuları listele
    topics = TopicContent.objects.filter(is_active=True).select_related('subject')
    subjects = Subject.objects.filter(is_active=True)
    
    context = {
        'topics': topics,
        'subjects': subjects,
        'title': 'Eğitim Oluştur'
    }
    
    return render(request, 'core/create_education.html', context)


@login_required
def education_session_detail(request, session_id):
    """Eğitim oturumu detay sayfası"""
    session = get_object_or_404(EducationSession, id=session_id, user=request.user)
    session.increment_view_count()
    
    context = {
        'session': session,
        'title': session.title
    }
    
    return render(request, 'core/education_session_detail.html', context)


def generate_education_content_with_ai(session):
    """AI ile eğitim içeriği oluştur"""
    try:
        from .utils import get_gemini_response
        
        prompt = f"""
        {session.topic.title} konusu hakkında {session.get_education_type_display().lower()} formatında eğitim içeriği oluştur.
        
        Konu açıklaması: {session.topic.description}
        Konu içeriği: {session.topic.content[:1000]}...
        
        Zorluk seviyesi: {session.get_difficulty_level_display()}
        Tahmini süre: {session.estimated_duration} dakika
        Dil: {session.get_language_display()}
        
        Lütfen konuyu adım adım, anlaşılır şekilde açıkla.
        {"İnternet araştırması yapmaya gerek yok, mevcut bilgileri kullan." if not session.use_internet_search else "Güncel bilgileri de ekleyebilirsin."}
        """
        
        content = get_gemini_response(prompt, session.user)
        return content
        
    except Exception as e:
        return f"Eğitim içeriği oluşturulurken hata: {str(e)}"