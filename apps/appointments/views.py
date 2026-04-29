"""
Представления модуля записи пациентов.
Включает: выбор врача, просмотр слотов, бронирование, отмена,
личный кабинет врача, панель администратора клиники.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Specialty, TimeSlot, Appointment, Schedule, Room
from apps.accounts.models import DoctorProfile, User
from apps.notifications.services import (
    send_booking_confirmation,
    send_cancellation_notice,
)


# ══════════════════════════════════════════════════════════════════════════════
#  ПАЦИЕНТ — выбор врача и запись
# ══════════════════════════════════════════════════════════════════════════════

from functools import wraps

def admin_required(view_func):
    """Декоратор для проверки прав администратора клиники."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and
                (request.user.is_clinic_admin or request.user.is_sysadmin)):
            messages.error(request, 'Доступ только для администраторов клиники.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def doctor_required(view_func):
    """Декоратор для проверки прав врача."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_doctor:
            messages.error(request, 'Доступ только для врачей.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def doctor_list(request):
    """
    Список врачей с фильтрацией по специальности.
    Доступен без авторизации — пациент может посмотреть врачей заранее.
    """
    specialties = Specialty.objects.filter(is_active=True)
    specialty_id = request.GET.get('specialty')

    doctors = DoctorProfile.objects.filter(is_active=True).select_related(
        'user', 'specialty'
    )
    if specialty_id:
        doctors = doctors.filter(specialty_id=specialty_id)

    selected_specialty = None
    if specialty_id:
        selected_specialty = specialties.filter(pk=specialty_id).first()

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'selected_specialty': selected_specialty,
    }
    return render(request, 'appointments/doctor_list.html', context)


@login_required
def slot_list(request, doctor_profile_id):
    """
    Доступные временны́е слоты выбранного врача.
    Показываем только будущие свободные слоты.
    """
    doctor_profile = get_object_or_404(DoctorProfile, pk=doctor_profile_id, is_active=True)

    today = timezone.now().date()
    slots = (
        TimeSlot.objects
        .filter(
            doctor_profile=doctor_profile,
            date__gte=today,
            is_booked=False,
            is_blocked=False,
        )
        .select_related('room')
        .order_by('date', 'start_time')
    )

    # Группируем по дате для удобства отображения
    from itertools import groupby
    grouped = {}
    for slot in slots:
        grouped.setdefault(slot.date, []).append(slot)

    context = {
        'doctor_profile': doctor_profile,
        'grouped_slots': grouped,
    }
    return render(request, 'appointments/slot_list.html', context)


@login_required
def book_appointment(request, slot_id):
    """
    Бронирование слота.
    Используем транзакцию + select_for_update, чтобы исключить двойное бронирование.
    """
    slot = get_object_or_404(TimeSlot, pk=slot_id)

    # Проверка: пациент уже записан на этот слот?
    if Appointment.objects.filter(slot=slot, patient=request.user).exclude(status=Appointment.Status.CANCELLED).exists():
        messages.error(request, 'Вы уже записаны на этот слот.')
        return redirect('appointments:my_appointments')

    # Предварительная проверка (без блокировки)
    if not slot.is_available:
        messages.error(request, 'Этот слот уже занят или недоступен. Выберите другое время.')
        return redirect('appointments:slot_list', doctor_profile_id=slot.doctor_profile_id)

    if request.method == 'POST':
        complaint = request.POST.get('complaint', '').strip()

        try:
            with transaction.atomic():
                # Блокируем строку на время транзакции — защита от гонки
                locked_slot = TimeSlot.objects.select_for_update().get(pk=slot_id)

                if locked_slot.is_booked or locked_slot.is_blocked:
                    messages.error(request, 'К сожалению, слот только что заняли. Выберите другое время.')
                    return redirect('appointments:slot_list', doctor_profile_id=slot.doctor_profile_id)

                locked_slot.is_booked = True
                locked_slot.save(update_fields=['is_booked'])

                appointment = Appointment.objects.create(
                    patient=request.user,
                    slot=locked_slot,
                    complaint=complaint,
                    status=Appointment.Status.BOOKED,
                )

            # Отправляем письмо подтверждения (вне транзакции)
            send_booking_confirmation(appointment)
            messages.success(
                request,
                f'Вы успешно записаны на {slot.date.strftime("%d.%m.%Y")} '
                f'в {slot.start_time.strftime("%H:%M")}. '
                f'Подтверждение отправлено на e-mail.'
            )
            return redirect('appointments:my_appointments')

        except Exception as exc:
            messages.error(request, f'Ошибка при бронировании. Попробуйте ещё раз.')
            return redirect('appointments:slot_list', doctor_profile_id=slot.doctor_profile_id)

    # GET — показываем страницу подтверждения
    context = {'slot': slot}
    return render(request, 'appointments/appointment_confirm.html', context)


@login_required
def my_appointments(request):
    """История и актуальные записи пациента."""
    appointments = (
        Appointment.objects
        .filter(patient=request.user)
        .select_related(
            'slot__doctor_profile__user',
            'slot__doctor_profile__specialty',
            'slot__room',
        )
        .order_by('-slot__date', '-slot__start_time')
    )
    context = {'appointments': appointments}
    return render(request, 'appointments/my_appointments.html', context)


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """Отмена записи пациентом."""
    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        patient=request.user,
    )

    if appointment.status in (Appointment.Status.CANCELLED, Appointment.Status.COMPLETED):
        messages.warning(request, 'Эта запись уже отменена или завершена.')
        return redirect('appointments:my_appointments')

    appointment.cancel()
    send_cancellation_notice(appointment)
    messages.success(request, 'Запись успешно отменена.')
    return redirect('appointments:my_appointments')


# ══════════════════════════════════════════════════════════════════════════════
#  ВРАЧ — личный кабинет
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def doctor_dashboard(request):
    """Личный кабинет врача — расписание на текущую дату и ближайшие дни."""
    if not request.user.is_doctor:
        messages.error(request, 'Доступ только для врачей.')
        return redirect('core:home')

    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    today = timezone.now().date()

    # Записи на сегодня
    todays_appointments = (
        Appointment.objects
        .filter(
            slot__doctor_profile=doctor_profile,
            slot__date=today,
        )
        .exclude(status=Appointment.Status.CANCELLED)
        .select_related('patient', 'slot__room')
        .order_by('slot__start_time')
    )

    # Предстоящие записи (следующие 14 дней)
    upcoming = (
        Appointment.objects
        .filter(
            slot__doctor_profile=doctor_profile,
            slot__date__gt=today,
            status=Appointment.Status.BOOKED,
        )
        .select_related('patient', 'slot__room')
        .order_by('slot__date', 'slot__start_time')[:20]
    )

    context = {
        'doctor_profile': doctor_profile,
        'todays_appointments': todays_appointments,
        'upcoming': upcoming,
        'today': today,
    }
    return render(request, 'doctor/dashboard.html', context)


@login_required
@require_POST
def mark_attendance(request, appointment_id):
    """Врач отмечает явку или неявку пациента."""
    if not request.user.is_doctor:
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        slot__doctor_profile__user=request.user,
    )
    action = request.POST.get('action')

    if action == 'attended':
        appointment.mark_attended()
        messages.success(request, f'Явка пациента {appointment.patient.full_name} отмечена.')
    elif action == 'no_show':
        appointment.mark_no_show()
        messages.warning(request, f'Неявка пациента {appointment.patient.full_name} отмечена.')
    else:
        messages.error(request, 'Неизвестное действие.')

    return redirect('appointments:doctor_dashboard')


@login_required
@require_POST
def block_slot(request, slot_id):
    """Врач блокирует слот (отпуск, учёба, личные дела)."""
    if not request.user.is_doctor:
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    slot = get_object_or_404(
        TimeSlot,
        pk=slot_id,
        doctor_profile__user=request.user,
        is_booked=False,
    )
    slot.is_blocked = not slot.is_blocked  # Переключатель
    slot.save(update_fields=['is_blocked'])
    status_text = 'заблокирован' if slot.is_blocked else 'разблокирован'
    messages.success(request, f'Слот {slot.start_time.strftime("%H:%M")} {status_text}.')
    return redirect('appointments:doctor_dashboard')


# ══════════════════════════════════════════════════════════════════════════════
#  АДМИНИСТРАТОР КЛИНИКИ — панель управления
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@admin_required
def admin_dashboard(request):

    today = timezone.now().date()

    # Сводка: записи сегодня
    todays_appointments = (
        Appointment.objects
        .filter(slot__date=today)
        .exclude(status=Appointment.Status.CANCELLED)
        .select_related(
            'patient',
            'slot__doctor_profile__user',
            'slot__doctor_profile__specialty',
            'slot__room',
        )
        .order_by('slot__start_time')
    )

    # Статистика
    stats = {
        'total_today': todays_appointments.count(),
        'total_doctors': DoctorProfile.objects.filter(is_active=True).count(),
        'total_rooms': Room.objects.filter(is_active=True).count(),
        'cancelled_today': Appointment.objects.filter(
            slot__date=today,
            status=Appointment.Status.CANCELLED,
        ).count(),
    }

    context = {
        'todays_appointments': todays_appointments,
        'stats': stats,
        'today': today,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@admin_required
def manage_schedule(request):
    """Администратор управляет расписанием врачей."""
    doctors = DoctorProfile.objects.filter(is_active=True).select_related('user', 'specialty')
    rooms = Room.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            doctor_id = request.POST.get('doctor_profile_id') or None
            room_id = request.POST.get('room_id') or None
            date_val = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            slot_duration = int(request.POST.get('slot_duration', 30))

            if not doctor_id:
                messages.error(request, 'Выберите врача.')
                return redirect('appointments:manage_schedule')

            schedule, created = Schedule.objects.update_or_create(
                doctor_profile_id=int(doctor_id),
                date=date_val,
                defaults={
                    'room_id': int(room_id) if room_id else None,
                    'start_time': start_time,
                    'end_time': end_time,
                    'slot_duration': slot_duration,
                }
            )
            action_text = 'создано' if created else 'обновлено'
            messages.success(request, f'Расписание {action_text} успешно. Слоты сгенерированы.')

        elif action == 'delete':
            schedule_id = request.POST.get('schedule_id')
            schedule = get_object_or_404(Schedule, pk=schedule_id)
            # Нельзя удалить расписание, если есть активные записи
            active = schedule.slots.filter(is_booked=True).count()
            if active:
                messages.error(request, f'Нельзя удалить расписание: {active} активных записей.')
            else:
                schedule.delete()
                messages.success(request, 'Расписание удалено.')

        return redirect('appointments:manage_schedule')

    # Расписания на ближайшие 30 дней
    from datetime import timedelta
    end_date = timezone.now().date() + timedelta(days=30)
    schedules = (
        Schedule.objects
        .filter(date__gte=timezone.now().date(), date__lte=end_date)
        .select_related('doctor_profile__user', 'doctor_profile__specialty', 'room')
        .order_by('date', 'start_time')
    )

    context = {
        'doctors': doctors,
        'rooms': rooms,
        'schedules': schedules,
    }
    return render(request, 'admin_panel/schedule_manage.html', context)


@login_required
@admin_required
def manage_rooms(request):
    """Администратор управляет кабинетами."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            Room.objects.create(
                number=request.POST.get('number'),
                name=request.POST.get('name', ''),
                floor=request.POST.get('floor', 1),
            )
            messages.success(request, 'Кабинет добавлен.')

        elif action == 'toggle':
            room = get_object_or_404(Room, pk=request.POST.get('room_id'))
            room.is_active = not room.is_active
            room.save(update_fields=['is_active'])
            messages.success(request, f'Кабинет {room.number} {"активирован" if room.is_active else "деактивирован"}.')

        return redirect('appointments:manage_rooms')

    rooms = Room.objects.all().order_by('number')
    context = {'rooms': rooms}
    return render(request, 'admin_panel/rooms_manage.html', context)


@login_required
@require_POST
@admin_required
def admin_cancel_appointment(request, appointment_id):
    """Администратор отменяет запись пациента."""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    appointment.cancel()
    send_cancellation_notice(appointment)
    messages.success(request, f'Запись пациента {appointment.patient.full_name} отменена.')
    return redirect('appointments:admin_dashboard')
