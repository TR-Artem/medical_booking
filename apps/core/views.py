"""Главная страница и общие представления."""
from django.shortcuts import render
from apps.appointments.models import Specialty
from apps.accounts.models import DoctorProfile


def home(request):
    """Главная страница — витрина клиники."""
    specialties = Specialty.objects.filter(is_active=True)[:8]
    doctors = DoctorProfile.objects.filter(is_active=True).select_related(
        'user', 'specialty'
    )[:6]
    context = {
        'specialties': specialties,
        'doctors': doctors,
    }
    return render(request, 'core/home.html', context)
