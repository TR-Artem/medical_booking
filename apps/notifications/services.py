"""
Сервис уведомлений.
Отправляет e-mail пациенту при бронировании, отмене и за 24 ч. до визита.
Задача напоминания запускается через Celery Beat.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def send_booking_confirmation(appointment):
    """
    Письмо подтверждения записи.
    Отправляется сразу после успешного бронирования.
    """
    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile

    subject = f'Подтверждение записи — {slot.date.strftime("%d.%m.%Y")}'
    message = (
        f'Здравствуйте, {patient.first_name}!\n\n'
        f'Вы успешно записались на приём:\n'
        f'  Врач:           {doctor.user.full_name}\n'
        f'  Специальность:   {doctor.specialty.name}\n'
        f'  Дата:           {slot.date.strftime("%d.%m.%Y")}\n'
        f'  Время:          {slot.start_time.strftime("%H:%M")} — {slot.end_time.strftime("%H:%M")}\n'
        f'  Кабинет:        {slot.room or "уточняется"}\n\n'
        f'Напоминание придёт за 24 часа до визита.\n\n'
        f'Если вам нужно отменить запись, сделайте это в личном кабинете:\n'
        f'{settings.SITE_URL}/appointments/my/\n\n'
        f'С уважением,\nМедицинский центр'
    )

    _send(subject, message, patient.email)


def send_cancellation_notice(appointment):
    """
    Письмо об отмене записи.
    Отправляется при отмене пациентом или администратором.
    """
    patient = appointment.patient
    slot = appointment.slot

    subject = f'Запись отменена — {slot.date.strftime("%d.%m.%Y")}'
    message = (
        f'Здравствуйте, {patient.first_name}!\n\n'
        f'Ваша запись на {slot.date.strftime("%d.%m.%Y")} в {slot.start_time.strftime("%H:%M")} '
        f'к врачу {slot.doctor_profile.user.full_name} отменена.\n\n'
        f'Вы можете записаться на другое время:\n'
        f'{settings.SITE_URL}/appointments/doctors/\n\n'
        f'С уважением,\nМедицинский центр'
    )

    _send(subject, message, patient.email)


def send_reminder(appointment):
    """
    Напоминание о визите за 24 часа.
    Вызывается Celery-задачей.
    """
    if appointment.reminder_sent:
        return  # Уже отправлено

    patient = appointment.patient
    slot = appointment.slot
    doctor = slot.doctor_profile

    subject = f'Напоминание о визите завтра — {slot.date.strftime("%d.%m.%Y")}'
    message = (
        f'Здравствуйте, {patient.first_name}!\n\n'
        f'Напоминаем о вашем визите ЗАВТРА:\n'
        f'  Врач:    {doctor.user.full_name}\n'
        f'  Время:   {slot.start_time.strftime("%H:%M")}\n'
        f'  Кабинет: {slot.room or "уточняется"}\n\n'
        f'Если не сможете прийти — пожалуйста, отмените запись заранее:\n'
        f'{settings.SITE_URL}/appointments/my/\n\n'
        f'С уважением,\nМедицинский центр'
    )

    _send(subject, message, patient.email)

    appointment.reminder_sent = True
    appointment.save(update_fields=['reminder_sent'])


def _send(subject: str, message: str, recipient_email: str):
    """Внутренняя функция отправки с базовой обработкой ошибок."""
    if not recipient_email:
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        # В production заменить на logging
        print(f'[EMAIL ERROR] Не удалось отправить письмо на {recipient_email}: {exc}')
