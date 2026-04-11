from datetime import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm,
    UserProfileForm, CustomPasswordChangeForm
)
from .models import CustomUser
from worlds.models import World
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy


def landing_view(request):
    """Landing page для неавторизованных пользователей"""
    if request.user.is_authenticated:
        return redirect('worlds:library')
    return render(request, 'users/landing.html')


def register_view(request):
    """Регистрация пользователя"""
    if request.user.is_authenticated:
        return redirect('worlds:library')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')

            next_url = request.session.pop('next_url', None)
            if next_url:
                return redirect(next_url)
            return redirect('worlds:library')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


from django.utils import timezone

def login_view(request):
    """Авторизация"""
    if request.user.is_authenticated:
        return redirect('worlds:library')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Обновляем время последней активности
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
            messages.success(request, f'С возвращением, {user.username}!')

            next_url = request.session.pop('next_url', None)
            if next_url:
                return redirect(next_url)
            return redirect('worlds:library')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('users:login')


@login_required
def profile_view(request, username=None):
    """Просмотр профиля"""
    if username:
        user = get_object_or_404(CustomUser, username=username)
        is_own_profile = request.user == user
    else:
        user = request.user
        is_own_profile = True

    if request.user.is_authenticated:
        request.user.last_activity = timezone.now()
        request.user.save(update_fields=['last_activity'])

    worlds = user.worlds.all()

    paginator = Paginator(worlds, 12)
    page_number = request.GET.get('page')
    worlds_page = paginator.get_page(page_number)

    context = {
        'profile_user': user,
        'is_own_profile': is_own_profile,
        'worlds': worlds_page,
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit_view(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def password_change_view(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён!')
            return redirect('users:profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'users/password_change.html', {'form': form})


@login_required
def delete_account_view(request):
    """Удаление аккаунта"""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Аккаунт успешно удалён')
        return redirect('users:login')

    return render(request, 'users/delete_account.html')


def password_reset_request_view(request):
    """Запрос на восстановление пароля"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Используем стандартную Django функцию для отправки письма
            from django.contrib.auth.forms import PasswordResetForm
            from django.contrib.auth.models import User

            reset_form = PasswordResetForm({'email': email})
            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name='users/password_reset_email.html',
                    subject_template_name='users/password_reset_subject.txt'
                )
                messages.success(request,
                                 'Инструкции по восстановлению пароля отправлены на вашу почту (если такой email существует в системе).')
                return redirect('users:password_reset_done')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'users/password_reset.html', {'form': form})


def password_reset_done_view(request):
    """Страница после отправки письма"""
    return render(request, 'users/password_reset_done.html')


def password_reset_confirm_view(request, uidb64, token):
    """Подтверждение и установка нового пароля"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        validlink = True

        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Пароль успешно изменён! Теперь вы можете войти с новым паролем.')
                return redirect('users:password_reset_complete')
        else:
            form = CustomSetPasswordForm(user)
    else:
        validlink = False
        form = None

    return render(request, 'users/password_reset_confirm.html', {
        'form': form,
        'validlink': validlink,
    })


def password_reset_complete_view(request):
    """Страница успешного изменения пароля"""
    return render(request, 'users/password_reset_complete.html')