# Path: member/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views.generic import CreateView, UpdateView
from django.http import JsonResponse
import json
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, 
    UserUpdateForm, AIAvatarForm, RegisterStep1Form, RegisterStep2Form, RegisterStep3Form
)
from .models import UserProfile, AIAvatar, ChatMessage
from core.models import UserSolutionProgress

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'member/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('core:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Giriş Yap'
        return context


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('member:login')

    def get(self, request, *args, **kwargs):
        """
        GET isteği ile çıkış yapma işlevselliği.
        Django'nun varsayılan LogoutView'ı güvenlik nedeniyle sadece POST kabul eder.
        Bu metod, <a> linklerinden gelen GET istekleriyle de çıkış yapılabilmesini sağlar.
        """
        logout(request)
        messages.info(request, "Başarıyla çıkış yaptınız.")
        return redirect(self.get_next_page())


def register_step1(request):
    if request.method == 'POST':
        form = RegisterStep1Form(request.POST)
        if form.is_valid():
            request.session['register_step1'] = form.cleaned_data
            return redirect('member:register_step2')
    else:
        form = RegisterStep1Form()
    
    return render(request, 'member/register_step1.html', {
        'form': form,
        'step': 1,
        'title': 'Kayıt Ol - Adım 1'
    })


def register_step2(request):
    if 'register_step1' not in request.session:
        return redirect('member:register_step1')
    
    if request.method == 'POST':
        form = RegisterStep2Form(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            
            if password1 != password2:
                messages.error(request, 'Şifreler eşleşmiyor!')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Bu kullanıcı adı zaten alınmış!')
            else:
                request.session['register_step2'] = form.cleaned_data
                return redirect('member:register_step3')
    else:
        form = RegisterStep2Form()
    
    return render(request, 'member/register_step2.html', {
        'form': form,
        'step': 2,
        'title': 'Kayıt Ol - Adım 2'
    })


def register_step3(request):
    if 'register_step1' not in request.session or 'register_step2' not in request.session:
        return redirect('member:register_step1')
    
    if request.method == 'POST':
        form = RegisterStep3Form(request.POST, request.FILES)
        if form.is_valid():
            request.session['register_step3'] = {
                'gender': form.cleaned_data['gender'],
                'birth_date': form.cleaned_data['birth_date'].isoformat() if form.cleaned_data['birth_date'] else None,
            }
            
            if form.cleaned_data['avatar']:
                request.session['has_avatar'] = True
            
            return redirect('member:register_step4')
    else:
        form = RegisterStep3Form()
    
    return render(request, 'member/register_step3.html', {
        'form': form,
        'step': 3,
        'title': 'Kayıt Ol - Adım 3'
    })


def register_step4(request):
    if not all(step in request.session for step in ['register_step1', 'register_step2', 'register_step3']):
        return redirect('member:register_step1')
    
    if request.method == 'POST':
        try:
            step1_data = request.session['register_step1']
            step2_data = request.session['register_step2']
            step3_data = request.session['register_step3']
            
            user = User.objects.create_user(
                username=step2_data['username'],
                email=step1_data['email'],
                password=step2_data['password1'],
                first_name=step1_data['first_name'],
                last_name=step1_data['last_name']
            )
            
            profile = user.profile
            profile.gender = step3_data['gender']
            if step3_data['birth_date']:
                from datetime import datetime
                profile.birth_date = datetime.fromisoformat(step3_data['birth_date']).date()
            profile.save()
            
            for key in ['register_step1', 'register_step2', 'register_step3', 'has_avatar']:
                request.session.pop(key, None)
            
            login(request, user)
            messages.success(request, 'Hoş geldiniz! Hesabınız başarıyla oluşturuldu.')
            return redirect('core:dashboard')
            
        except Exception as e:
            messages.error(request, 'Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.')
            return redirect('member:register_step1')
    
    context = {
        'step1_data': request.session.get('register_step1', {}),
        'step2_data': request.session.get('register_step2', {}),
        'step3_data': request.session.get('register_step3', {}),
        'step': 4,
        'title': 'Kayıt Ol - Onay'
    }
    
    return render(request, 'member/register_step4.html', context)


@login_required
def profile_view(request):
    user_form = UserUpdateForm(instance=request.user)
    profile_form = UserProfileForm(instance=request.user.profile)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profiliniz başarıyla güncellendi!')
            return redirect('member:profile')
    
    completed_solutions_count = UserSolutionProgress.objects.filter(user=request.user, is_completed=True).count()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'completed_solutions_count': completed_solutions_count,
        'title': 'Profil Ayarları'
    }
    
    return render(request, 'member/profile.html', context)


@login_required
def avatar_create(request):
    try:
        avatar = request.user.ai_avatar
        form = AIAvatarForm(instance=avatar)
    except AIAvatar.DoesNotExist:
        form = AIAvatarForm()
        avatar = None
    
    if request.method == 'POST':
        if avatar:
            form = AIAvatarForm(request.POST, request.FILES, instance=avatar)
        else:
            form = AIAvatarForm(request.POST, request.FILES)
        
        if form.is_valid():
            avatar = form.save(commit=False)
            avatar.user = request.user
            avatar.save()
            messages.success(request, 'Avatar başarıyla oluşturuldu!')
            return redirect('member:avatar_chat')
    
    return render(request, 'member/avatar_create.html', {
        'form': form,
        'avatar': avatar,
        'title': 'Avatar Oluştur'
    })


@login_required
def avatar_chat(request):
    try:
        avatar = request.user.ai_avatar
    except AIAvatar.DoesNotExist:
        messages.warning(request, 'Önce bir avatar oluşturmalısınız!')
        return redirect('member:avatar_create')
    
    messages_list = ChatMessage.objects.filter(user=request.user)[:50]
    
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        data = json.loads(request.body)
        message_text = data.get('message', '')
        
        if message_text:
            user_message = ChatMessage.objects.create(
                user=request.user,
                message=message_text,
                is_bot_response=False
            )
            
            bot_responses = [
                "Merhaba! Size nasıl yardımcı olabilirim?",
                "Bu çok ilginç bir soru! Biraz düşüneyim...",
                "Anlıyorum. Bu konuda size yardımcı olmaya çalışacağım.",
                "Harika! Bu sorunun cevabını biliyor olabilirim.",
                "Mükemmel soru! Birlikte çözelim."
            ]
            
            import random
            bot_response = ChatMessage.objects.create(
                user=request.user,
                message=random.choice(bot_responses),
                is_bot_response=True
            )
            
            return JsonResponse({
                'success': True,
                'user_message': {
                    'id': user_message.id,
                    'message': user_message.message,
                    'timestamp': user_message.created_at.strftime('%H:%M')
                },
                'bot_response': {
                    'id': bot_response.id,
                    'message': bot_response.message,
                    'timestamp': bot_response.created_at.strftime('%H:%M')
                }
            })
    
    return render(request, 'member/avatar_chat.html', {
        'avatar': avatar,
        'messages': messages_list,
        'title': 'Avatar ile Sohbet'
    })


@login_required
def dashboard(request):
    total_messages = ChatMessage.objects.filter(user=request.user).count()
    
    context = {
        'user': request.user,
        'total_messages': total_messages,
        'title': 'Kontrol Paneli'
    }
    
    return render(request, 'member/dashboard.html', context)


def register_check_username(request):
    if request.method == 'GET':
        username = request.GET.get('username', '')
        is_available = not User.objects.filter(username=username).exists() if username else False
        return JsonResponse({'available': is_available})
    return JsonResponse({'available': False})


def register_check_email(request):
    if request.method == 'GET':
        email = request.GET.get('email', '')
        is_available = not User.objects.filter(email=email).exists() if email else False
        return JsonResponse({'available': is_available})