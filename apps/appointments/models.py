"""
Модели модуля записи:
  Specialty  — специальность врача
  Room       — кабинет
  Schedule   — рабочий день врача (генерирует временны́е слоты)
  TimeSlot   — конкретный временной слот приёма
  Appointment — запись пациента на слот
"""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Specialty(models.Model):
    """Справочник специальностей врачей."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Специальность")
    description = models.TextField(blank=True, verbose_name="Описание")
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Bootstrap-иконка (bi-...)",
        help_text="Например: bi-heart-pulse",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Room(models.Model):
    """Кабинет приёма."""

    number = models.CharField(max_length=10, unique=True, verbose_name="Номер кабинета")
    name = models.CharField(max_length=100, blank=True, verbose_name="Название / профиль")
    floor = models.PositiveSmallIntegerField(default=1, verbose_name="Этаж")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"
        ordering = ["number"]

    def __str__(self):
        return f'Каб. {self.number} — {self.name or "без названия"}'


class Schedule(models.Model):
    """
    Расписание рабочего дня врача.
    Администратор создаёт запись Schedule, система автоматически
    генерирует TimeSlot-ы при сохранении.
    """

    doctor_profile = models.ForeignKey(
        "accounts.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Врач",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedules",
        verbose_name="Кабинет",
    )
    date = models.DateField(verbose_name="Дата приёма")
    start_time = models.TimeField(verbose_name="Начало приёма")
    end_time = models.TimeField(verbose_name="Конец приёма")
    slot_duration = models.PositiveSmallIntegerField(
        default=30,
        verbose_name="Длительность слота (мин)",
    )

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"
        ordering = ["date", "start_time"]
        # Один врач не может вести приём в двух кабинетах одновременно
        unique_together = [("doctor_profile", "date")]

    def __str__(self):
        return f"{self.doctor_profile} | {self.date} {self.start_time}–{self.end_time}"

    def save(self, *args, **kwargs):
        # Валидация перед сохранением
        self.full_clean()
        super().save(*args, **kwargs)
        self._generate_slots()

    def _generate_slots(self):
        """Генерирует временны́е слоты на основе расписания."""
        from .services import generate_slots

        generate_slots(self)

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "Время окончания должно быть позже начала."})

        if self.room_id and self.date and self.start_time and self.end_time:
            overlapping = (
                Schedule.objects.filter(room_id=self.room_id, date=self.date)
                .exclude(pk=self.pk)
                .select_related("doctor_profile__user")
            )
            for other in overlapping:
                if self.start_time < other.end_time and other.start_time < self.end_time:
                    raise ValidationError(
                        {
                            "room": (
                                f"Кабинет {self.room.number} уже занят врачом "
                                f"{other.doctor_profile.user.full_name} "
                                f"с {other.start_time.strftime('%H:%M')} "
                                f"до {other.end_time.strftime('%H:%M')}."
                            )
                        }
                    )


class TimeSlot(models.Model):
    """Конкретный временной слот для записи к врачу."""

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="Расписание",
    )
    doctor_profile = models.ForeignKey(
        "accounts.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="Врач",
    )
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Начало")
    end_time = models.TimeField(verbose_name="Конец")
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Кабинет",
    )
    is_booked = models.BooleanField(default=False, verbose_name="Занят")
    # Врач может заблокировать слот (отпуск, учёба)
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован врачом")

    class Meta:
        verbose_name = "Временной слот"
        verbose_name_plural = "Временные слоты"
        ordering = ["date", "start_time"]
        # Гарантия уникальности: один слот — один врач — одно время
        unique_together = [("doctor_profile", "date", "start_time")]

    def __str__(self):
        return (
            f"{self.doctor_profile.user.full_name} | {self.date} {self.start_time}–{self.end_time}"
        )

    @property
    def start_at(self):
        """Начало приёма как aware-datetime в часовом поясе клиники."""
        return timezone.make_aware(
            datetime.combine(self.date, self.start_time),
            timezone.get_current_timezone(),
        )

    @property
    def is_past(self):
        return self.start_at <= timezone.now()

    @property
    def is_available(self):
        return not self.is_booked and not self.is_blocked and not self.is_past

    @property
    def datetime_start(self):
        return self.start_at


class Appointment(models.Model):
    """Запись пациента на приём."""

    class Status(models.TextChoices):
        BOOKED = "booked", "Забронировано"
        CONFIRMED = "confirmed", "Подтверждено"
        CANCELLED = "cancelled", "Отменено"
        COMPLETED = "completed", "Завершено (пациент явился)"
        NO_SHOW = "no_show", "Неявка"

    patient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Пациент",
        limit_choices_to={"role": "patient"},
    )
    slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Временной слот",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.BOOKED,
        verbose_name="Статус",
    )
    complaint = models.TextField(blank=True, verbose_name="Жалоба / причина визита")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    # Флаг: напоминание за 24 ч. отправлено
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ["-created_at"]
        constraints = [
            # На один слот может быть только одна активная запись.
            # Отменённые, завершённые и неявившиеся записи остаются в истории.
            models.UniqueConstraint(
                fields=["slot"],
                condition=models.Q(status__in=["booked", "confirmed"]),
                name="unique_active_appointment_per_slot",
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="appt_status_idx"),
            models.Index(fields=["patient", "-created_at"], name="appt_patient_created_idx"),
        ]

    def __str__(self):
        return (
            f"{self.patient.full_name} → "
            f"{self.slot.doctor_profile.user.full_name} | "
            f"{self.slot.date} {self.slot.start_time} [{self.get_status_display()}]"
        )

    def cancel(self):
        """Отменить запись и освободить слот."""
        self.status = self.Status.CANCELLED
        self.slot.is_booked = False
        self.slot.save(update_fields=["is_booked"])
        self.save(update_fields=["status", "updated_at"])

    def confirm(self):
        """Подтвердить запись (администратор или врач)."""
        self.status = self.Status.CONFIRMED
        self.save(update_fields=["status", "updated_at"])

    def mark_attended(self):
        """Отметить явку пациента."""
        self.status = self.Status.COMPLETED
        self.save(update_fields=["status", "updated_at"])

    def mark_no_show(self):
        """Отметить неявку пациента."""
        self.status = self.Status.NO_SHOW
        self.save(update_fields=["status", "updated_at"])
