"""Главная страница, служебные страницы и health-check."""

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.models import DoctorProfile
from apps.appointments.models import Specialty


def home(request):
    """Главная страница — витрина клиники."""
    specialties = Specialty.objects.filter(is_active=True)[:8]
    doctors = DoctorProfile.objects.filter(is_active=True).select_related("user", "specialty")[:6]
    context = {
        "specialties": specialties,
        "doctors": doctors,
    }
    return render(request, "core/home.html", context)


def privacy(request):
    """Политика обработки персональных данных и текст согласия (152-ФЗ)."""
    return render(request, "core/privacy.html")


def healthz(request):
    """Health-check для мониторинга: приложение и БД."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception:
        db_ok = False

    payload = {
        "status": "ok" if db_ok else "error",
        "db": db_ok,
        "version": settings.APP_VERSION,
    }
    return JsonResponse(payload, status=200 if db_ok else 503)


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
