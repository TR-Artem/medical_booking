"""
Celery-задачи модуля уведомлений.
Запускаются из представлений и по расписанию через django-celery-beat.
"""

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.appointments.models import Appointment

from .services import send_booking_confirmation, send_cancellation_notice, send_reminder


def _appointment_queryset():
    return Appointment.objects.select_related(
        "patient",
        "slot__doctor_profile__user",
        "slot__doctor_profile__specialty",
        "slot__room",
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_booking_confirmation_task(self, appointment_id):
    """Подтверждение записи. Повторяет отправку при ошибке SMTP."""
    appointment = _appointment_queryset().filter(pk=appointment_id).first()
    if appointment is None:
        return "Запись не найдена"
    send_booking_confirmation(appointment)
    return f"Подтверждение отправлено: {appointment_id}"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_cancellation_notice_task(self, appointment_id):
    """Уведомление об отмене."""
    appointment = _appointment_queryset().filter(pk=appointment_id).first()
    if appointment is None:
        return "Запись не найдена"
    send_cancellation_notice(appointment)
    return f"Уведомление об отмене отправлено: {appointment_id}"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_appointment_reminders(self):
    """Напоминания пациентам, у которых визит через 23–25 часов."""
    now = timezone.now()
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=25)

    appointments = _appointment_queryset().filter(
        status__in=[Appointment.Status.BOOKED, Appointment.Status.CONFIRMED],
        reminder_sent=False,
        slot__date__in=[window_start.date(), window_end.date()],
    )

    sent = 0
    for appointment in appointments:
        if window_start <= appointment.slot.start_at <= window_end:
            if send_reminder(appointment):
                sent += 1

    return f"Отправлено напоминаний: {sent}"
