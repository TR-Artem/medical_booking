"""
Представления модуля авторизации и профилей.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import PatientRegistrationForm, LoginForm, ProfileUpdateForm
from .models import User


class RegisterView(CreateView):
    """Регистрация нового пациента."""
    form_class = PatientRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно.')
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)


def login_view(request):
    """Вход в систему."""
    if request.user.is_authenticated:
        return redirect('core:home')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            # Редирект по роли
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_by_role(user)
        else:
            messages.error(request, 'Неверный логин или пароль.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Выход из системы."""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """Просмотр и редактирование профиля пользователя."""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {'form': form}

    # Дополнительный контекст для пациента — история записей
    if request.user.is_patient:
        from apps.appointments.models import Appointment
        context['appointments'] = (
            Appointment.objects
            .filter(patient=request.user)
            .select_related('slot__doctor_profile__user', 'slot__doctor_profile__specialty')
            .order_by('-slot__date', '-slot__start_time')[:10]
        )

    return render(request, 'accounts/profile.html', context)


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _redirect_by_role(user: User):
    """Перенаправление пользователя после входа в зависимости от роли."""
    if user.is_doctor:
        return redirect('appointments:doctor_dashboard')
    elif user.is_clinic_admin or user.is_sysadmin:
        return redirect('appointments:admin_dashboard')
    return redirect('core:home')
