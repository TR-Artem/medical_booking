"""
Сервис уведомлений.

Формирует и отправляет письма. Вызывается из Celery-задач
(apps/notifications/tasks.py), поэтому сетевые ошибки не перехватываются:
задача повторяет попытку с backoff.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send_email(*, subject, text_content, html_template, context, recipient):
    if not recipient:
        logger.warning("Не указан e-mail получателя, письмо не отправлено")
        return

    html_content = render_to_string(html_template, context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
    logger.info("Письмо отправлено: %s (%s)", recipient, subject)


def send_booking_confirmation(appointment):
    """Письмо подтверждения записи."""
    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile
    subject = f'Подтверждение записи — {slot.date.strftime("%d.%m.%Y")}'

    context = {
        "subject": subject,
        "patient_name": patient.first_name or patient.username,
        "doctor_name": doctor.user.full_name,
        "specialty": doctor.specialty.name,
        "date": slot.date.strftime("%d.%m.%Y"),
        "time": f'{slot.start_time.strftime("%H:%M")} — {slot.end_time.strftime("%H:%M")}',
        "room": str(slot.room) if slot.room else "Уточняется",
        "site_url": settings.SITE_URL,
    }
    text_content = f"""Здравствуйте, {patient.first_name}!

Вы успешно записаны на приём:

Врач: {doctor.user.full_name}
Специальность: {doctor.specialty.name}
Дата: {slot.date.strftime('%d.%m.%Y')}
Время: {slot.start_time.strftime('%H:%M')} — {slot.end_time.strftime('%H:%M')}
Кабинет: {slot.room or 'уточняется'}

Напоминание придёт за 24 часа до визита.

Если вам нужно отменить запись:
{settings.SITE_URL}/appointments/my/

С уважением,
Медицинский центр"""

    _send_email(
        subject=subject,
        text_content=text_content,
        html_template="notifications/booking_confirmation.html",
        context=context,
        recipient=patient.email,
    )


def send_cancellation_notice(appointment):
    """Письмо об отмене записи."""
    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile
    subject = f'Запись отменена — {slot.date.strftime("%d.%m.%Y")}'

    context = {
        "subject": subject,
        "patient_name": patient.first_name or patient.username,
        "doctor_name": doctor.user.full_name,
        "date": slot.date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
        "site_url": settings.SITE_URL,
    }
    text_content = f"""Здравствуйте, {patient.first_name}!

Ваша запись на приём отменена:

Врач: {doctor.user.full_name}
Дата: {slot.date.strftime('%d.%m.%Y')}
Время: {slot.start_time.strftime('%H:%M')}

Вы можете записаться на другое время:
{settings.SITE_URL}/appointments/doctors/

С уважением,
Медицинский центр"""

    _send_email(
        subject=subject,
        text_content=text_content,
        html_template="notifications/cancellation.html",
        context=context,
        recipient=patient.email,
    )


def send_reminder(appointment):
    """Напоминание о визите за 24 часа. Возвращает True, если письмо ушло."""
    if appointment.reminder_sent:
        logger.info("Напоминание уже отправлено для записи %s", appointment.id)
        return False

    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile
    subject = f'Напоминание о визите завтра — {slot.date.strftime("%d.%m.%Y")}'

    context = {
        "subject": subject,
        "patient_name": patient.first_name or patient.username,
        "doctor_name": doctor.user.full_name,
        "date": slot.date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
        "room": str(slot.room) if slot.room else "Уточняется",
        "site_url": settings.SITE_URL,
    }
    text_content = f"""Здравствуйте, {patient.first_name}!

Напоминаем о вашем визите ЗАВТРА:

Врач: {doctor.user.full_name}
Дата: {slot.date.strftime('%d.%m.%Y')}
Время: {slot.start_time.strftime('%H:%M')}
Кабинет: {slot.room or 'уточняется'}

Если не сможете прийти — пожалуйста, отмените запись заранее:
{settings.SITE_URL}/appointments/my/

С уважением,
Медицинский центр"""

    _send_email(
        subject=subject,
        text_content=text_content,
        html_template="notifications/reminder.html",
        context=context,
        recipient=patient.email,
    )

    appointment.reminder_sent = True
    appointment.save(update_fields=["reminder_sent"])
    return True
