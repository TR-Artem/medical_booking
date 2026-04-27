"""
Модели модуля записи:
  Specialty  — специальность врача
  Room       — кабинет
  Schedule   — рабочий день врача (генерирует временны́е слоты)
  TimeSlot   — конкретный временной слот приёма
  Appointment — запись пациента на слот
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime, date, time


class Specialty(models.Model):
    """Справочник специальностей врачей."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Специальность')
    description = models.TextField(blank=True, verbose_name='Описание')
    icon = models.CharField(
        max_length=50, blank=True,
        verbose_name='Bootstrap-иконка (bi-...)',
        help_text='Например: bi-heart-pulse',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'
        ordering = ['name']

    def __str__(self):
        return self.name


class Room(models.Model):
    """Кабинет приёма."""
    number = models.CharField(max_length=10, unique=True, verbose_name='Номер кабинета')
    name = models.CharField(max_length=100, blank=True, verbose_name='Название / профиль')
    floor = models.PositiveSmallIntegerField(default=1, verbose_name='Этаж')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'
        ordering = ['number']

    def __str__(self):
        return f'Каб. {self.number} — {self.name or "без названия"}'


class Schedule(models.Model):
    """
    Расписание рабочего дня врача.
    Администратор создаёт запись Schedule, система автоматически
    генерирует TimeSlot-ы при сохранении.
    """
    doctor_profile = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Врач',
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='schedules',
        verbose_name='Кабинет',
    )
    date = models.DateField(verbose_name='Дата приёма')
    start_time = models.TimeField(verbose_name='Начало приёма')
    end_time = models.TimeField(verbose_name='Конец приёма')
    slot_duration = models.PositiveSmallIntegerField(
        default=30,
        verbose_name='Длительность слота (мин)',
    )

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['date', 'start_time']
        # Один врач не может вести приём в двух кабинетах одновременно
        unique_together = [('doctor_profile', 'date')]

    def __str__(self):
        return f'{self.doctor_profile} | {self.date} {self.start_time}–{self.end_time}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._generate_slots()

    def _generate_slots(self):
        """Генерирует временны́е слоты на основе расписания."""
        # Удаляем только свободные слоты (занятые не трогаем)
        self.slots.filter(is_booked=False).delete()

        # Преобразуем строки в нужные типы если пришли из POST
        slot_date = self.date
        slot_start = self.start_time
        slot_end = self.end_time

        if isinstance(slot_date, str):
            from datetime import date as date_type
            slot_date = date_type.fromisoformat(slot_date)
        if isinstance(slot_start, str):
            from datetime import time as time_type
            h, m = slot_start.split(':')[:2]
            slot_start = time_type(int(h), int(m))
        if isinstance(slot_end, str):
            from datetime import time as time_type
            h, m = slot_end.split(':')[:2]
            slot_end = time_type(int(h), int(m))

        start = datetime.combine(slot_date, slot_start)
        end = datetime.combine(slot_date, slot_end)
        delta = timedelta(minutes=self.slot_duration)

        current = start
        slots_to_create = []
        while current + delta <= end:
            # Не создаём слот, если он уже существует (занятый)
            if not self.slots.filter(start_time=current.time()).exists():
                slots_to_create.append(
                    TimeSlot(
                        schedule=self,
                        doctor_profile=self.doctor_profile,
                        date=self.date,
                        start_time=current.time(),
                        end_time=(current + delta).time(),
                        room=self.room,
                    )
                )
            current += delta

        TimeSlot.objects.bulk_create(slots_to_create)


class TimeSlot(models.Model):
    """Конкретный временной слот для записи к врачу."""
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='slots',
        verbose_name='Расписание',
    )
    doctor_profile = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='slots',
        verbose_name='Врач',
    )
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Начало')
    end_time = models.TimeField(verbose_name='Конец')
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Кабинет',
    )
    is_booked = models.BooleanField(default=False, verbose_name='Занят')
    # Врач может заблокировать слот (отпуск, учёба)
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован врачом')

    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        ordering = ['date', 'start_time']
        # Гарантия уникальности: один слот — один врач — одно время
        unique_together = [('doctor_profile', 'date', 'start_time')]

    def __str__(self):
        return f'{self.doctor_profile.user.full_name} | {self.date} {self.start_time}–{self.end_time}'

    @property
    def is_available(self):
        return not self.is_booked and not self.is_blocked and self.date >= date.today()

    @property
    def datetime_start(self):
        return datetime.combine(self.date, self.start_time)


class Appointment(models.Model):
    """Запись пациента на приём."""

    class Status(models.TextChoices):
        BOOKED    = 'booked',    'Забронировано'
        CONFIRMED = 'confirmed', 'Подтверждено'
        CANCELLED = 'cancelled', 'Отменено'
        COMPLETED = 'completed', 'Завершено (пациент явился)'
        NO_SHOW   = 'no_show',   'Неявка'

    patient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Пациент',
        limit_choices_to={'role': 'patient'},
    )
    slot = models.OneToOneField(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='appointment',
        verbose_name='Временной слот',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.BOOKED,
        verbose_name='Статус',
    )
    complaint = models.TextField(blank=True, verbose_name='Жалоба / причина визита')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    # Флаг: напоминание за 24 ч. отправлено
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'{self.patient.full_name} → '
            f'{self.slot.doctor_profile.user.full_name} | '
            f'{self.slot.date} {self.slot.start_time} [{self.get_status_display()}]'
        )

    def cancel(self):
        """Отменить запись и освободить слот."""
        self.status = self.Status.CANCELLED
        self.slot.is_booked = False
        self.slot.save(update_fields=['is_booked'])
        self.save(update_fields=['status', 'updated_at'])

    def mark_attended(self):
        """Отметить явку пациента."""
        self.status = self.Status.COMPLETED
        self.save(update_fields=['status', 'updated_at'])

    def mark_no_show(self):
        """Отметить неявку пациента."""
        self.status = self.Status.NO_SHOW
        self.save(update_fields=['status', 'updated_at'])
