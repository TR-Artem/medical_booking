"""
Сервис уведомлений.
Отправляет e-mail пациенту при бронировании, отмене и за 24 ч. до визита.
Задача напоминания запускается через Celery Beat.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_booking_confirmation(appointment):
    """
    Письмо подтверждения записи.
    Отправляется сразу после успешного бронирования.
    HTML-шаблон: templates/notifications/booking_confirmation.html
    """
    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile

    subject = f'Подтверждение записи — {slot.date.strftime("%d.%m.%Y")}'

    # Контекст для шаблона
    context = {
        'subject': subject,
        'patient_name': patient.first_name or patient.username,
        'doctor_name': doctor.user.full_name,
        'specialty': doctor.specialty.name,
        'date': slot.date.strftime('%d.%m.%Y'),
        'time': f'{slot.start_time.strftime("%H:%M")} — {slot.end_time.strftime("%H:%M")}',
        'room': str(slot.room) if slot.room else 'Уточняется',
        'site_url': settings.SITE_URL,
    }

    try:
        # Отправляем HTML
        html_content = render_to_string('notifications/booking_confirmation.html', context)
        # Отправляем plaintext (резервный)
        text_content = f'''Здравствуйте, {patient.first_name}!

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
Медицинский центр'''

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient.email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(f'Письмо подтверждения отправлено: {patient.email}')

    except Exception as exc:
        logger.error(f'Ошибка отправки письма подтверждения на {patient.email}: {exc}')


def send_cancellation_notice(appointment):
    """
    Письмо об отмене записи.
    Отправляется при отмене пациентом или администратором.
    HTML-шаблон: templates/notifications/cancellation.html
    """
    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile

    subject = f'Запись отменена — {slot.date.strftime("%d.%m.%Y")}'

    context = {
        'subject': subject,
        'patient_name': patient.first_name or patient.username,
        'doctor_name': doctor.user.full_name,
        'date': slot.date.strftime('%d.%m.%Y'),
        'time': slot.start_time.strftime('%H:%M'),
        'site_url': settings.SITE_URL,
    }

    try:
        html_content = render_to_string('notifications/cancellation.html', context)
        text_content = f'''Здравствуйте, {patient.first_name}!

Ваша запись на приём отменена:

Врач: {doctor.user.full_name}
Дата: {slot.date.strftime('%d.%m.%Y')}
Время: {slot.start_time.strftime('%H:%M')}

Вы можете записаться на другое время:
{settings.SITE_URL}/appointments/doctors/

С уважением,
Медицинский центр'''

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient.email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(f'Письмо об отмене отправлено: {patient.email}')

    except Exception as exc:
        logger.error(f'Ошибка отправки письма об отмене на {patient.email}: {exc}')


def send_reminder(appointment):
    """
    Напоминание о визите за 24 часа.
    Вызывается Celery-задачей.
    HTML-шаблон: templates/notifications/reminder.html
    """
    if appointment.reminder_sent:
        logger.info(f'Напоминание уже отправлено для записи {appointment.id}')
        return

    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile

    subject = f'Напоминание о визите завтра — {slot.date.strftime("%d.%m.%Y")}'

    context = {
        'subject': subject,
        'patient_name': patient.first_name or patient.username,
        'doctor_name': doctor.user.full_name,
        'date': slot.date.strftime('%d.%m.%Y'),
        'time': slot.start_time.strftime('%H:%M'),
        'room': str(slot.room) if slot.room else 'Уточняется',
        'site_url': settings.SITE_URL,
    }

    try:
        html_content = render_to_string('notifications/reminder.html', context)
        text_content = f'''Здравствуйте, {patient.first_name}!

Напоминаем о вашем визите ЗАВТРА:

Врач: {doctor.user.full_name}
Дата: {slot.date.strftime('%d.%m.%Y')}
Время: {slot.start_time.strftime('%H:%M')}
Кабинет: {slot.room or 'уточняется'}

Если не сможете прийти — пожалуйста, отмените запись заранее:
{settings.SITE_URL}/appointments/my/

С уважением,
Медицинский центр'''

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient.email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        # Отмечаем что напоминание отправлено
        appointment.reminder_sent = True
        appointment.save(update_fields=['reminder_sent'])

        logger.info(f'Напоминание отправлено: {patient.email}')

    except Exception as exc:
        logger.error(f'Ошибка отправки напоминания на {patient.email}: {exc}')
