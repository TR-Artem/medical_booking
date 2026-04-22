"""
Celery-задачи модуля уведомлений.
Запускаются по расписанию через django-celery-beat.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_appointment_reminders():
    """
    Отправляет напоминания пациентам, у которых визит через 24 ч.
    Запускать каждый час через Celery Beat:
      crontab(minute=0)  — каждый час в :00
    """
    from apps.appointments.models import Appointment
    from .services import send_reminder

    now = timezone.now()
    # Окно: визит от 23 до 25 часов с текущего момента
    window_start = now + timedelta(hours=23)
    window_end   = now + timedelta(hours=25)

    appointments = Appointment.objects.filter(
        status=Appointment.Status.BOOKED,
        reminder_sent=False,
        slot__date=window_start.date(),
    ).select_related('patient', 'slot__doctor_profile__user', 'slot__room')

    sent = 0
    for appt in appointments:
        # Дополнительная проверка по времени
        appt_dt = timezone.make_aware(
            __import__('datetime').datetime.combine(appt.slot.date, appt.slot.start_time)
        )
        if window_start <= appt_dt <= window_end:
            send_reminder(appt)
            sent += 1

    return f'Отправлено напоминаний: {sent}'
