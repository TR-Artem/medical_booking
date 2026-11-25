"""
Представления модуля авторизации и профилей.
"""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView

from .forms import LoginForm, PatientRegistrationForm, ProfileUpdateForm
from .models import User

logger = logging.getLogger(__name__)

LOGIN_MAX_ATTEMPTS_PER_ACCOUNT = 5
LOGIN_MAX_ATTEMPTS_PER_IP = 20
LOGIN_LOCKOUT_SECONDS = 15 * 60


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _counter_get(key):
    try:
        return int(cache.get(key, 0) or 0)
    except Exception:  # Redis недоступен — не блокируем вход из-за кэша
        logger.warning("Кэш недоступен, rate limit входа отключён")
        return 0


def _counter_incr(key):
    try:
        try:
            return cache.incr(key)
        except ValueError:
            cache.set(key, 1, LOGIN_LOCKOUT_SECONDS)
            return 1
    except Exception:
        return 0


def _counter_reset(key):
    try:
        cache.delete(key)
    except Exception:
        pass


class RegisterView(CreateView):
    """Регистрация нового пациента."""

    form_class = PatientRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request, f"Добро пожаловать, {user.first_name}! Регистрация прошла успешно."
        )
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)


def login_view(request):
    """Вход в систему по логину или e-mail, с защитой от перебора."""
    if request.user.is_authenticated:
        return redirect("core:home")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        ip = _client_ip(request)
        account_key = f"login:fail:account:{ip}:{username.lower()}"
        ip_key = f"login:fail:ip:{ip}"

        if (
            _counter_get(account_key) >= LOGIN_MAX_ATTEMPTS_PER_ACCOUNT
            or _counter_get(ip_key) >= LOGIN_MAX_ATTEMPTS_PER_IP
        ):
            logger.warning("Вход заблокирован rate limit: ip=%s login=%s", ip, username)
            messages.error(
                request,
                "Слишком много неудачных попыток входа. Повторите через 15 минут.",
            )
            return render(request, "accounts/login.html", {"form": form}, status=429)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            _counter_reset(account_key)
            logger.info("Вход выполнен: %s (ip=%s)", user.username, ip)
            messages.success(request, f"Добро пожаловать, {user.first_name or user.username}!")
            # Редирект по роли; внешние next не принимаем (open redirect).
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return _redirect_by_role(user)

        _counter_incr(account_key)
        _counter_incr(ip_key)
        logger.warning("Неудачный вход: ip=%s login=%s", ip, username)
        messages.error(request, "Неверный логин или пароль.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """Выход из системы."""
    if request.user.is_authenticated:
        logger.info("Выход: %s", request.user.username)
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("core:home")


@login_required
def profile_view(request):
    """Просмотр и редактирование профиля пользователя."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлён.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {"form": form}

    # Дополнительный контекст для пациента — история записей
    if request.user.is_patient:
        from apps.appointments.models import Appointment

        context["appointments"] = (
            Appointment.objects.filter(patient=request.user)
            .select_related("slot__doctor_profile__user", "slot__doctor_profile__specialty")
            .order_by("-slot__date", "-slot__start_time")[:10]
        )

    return render(request, "accounts/profile.html", context)


# ── Вспомогательные функции ───────────────────────────────────────────────────


def _redirect_by_role(user: User):
    """Перенаправление пользователя после входа в зависимости от роли."""
    if user.is_doctor:
        return redirect("appointments:doctor_dashboard")
    elif user.is_clinic_admin or user.is_sysadmin:
        return redirect("appointments:admin_dashboard")
    return redirect("core:home")
