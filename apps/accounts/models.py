"""
Модели пользователей системы.

Иерархия ролей:
  User (базовый)
    ├── PATIENT  — пациент
    ├── DOCTOR   — врач
    ├── ADMIN    — администратор / регистратор клиники
    └── SYSADMIN — системный администратор
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Расширенная модель пользователя.
    Наследует username, password, email, first_name, last_name от AbstractUser.
    """

    class Role(models.TextChoices):
        PATIENT  = 'patient',  'Пациент'
        DOCTOR   = 'doctor',   'Врач'
        ADMIN    = 'admin',    'Администратор клиники'
        SYSADMIN = 'sysadmin', 'Системный администратор'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT,
        verbose_name='Роль',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон',
    )
    # Согласие на обработку персональных данных (ФЗ-152)
    pd_consent = models.BooleanField(
        default=False,
        verbose_name='Согласие на обработку ПДн',
    )

    # ── вспомогательные свойства ──────────────────────────────────────────────
    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_clinic_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_sysadmin(self):
        return self.role == self.Role.SYSADMIN

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'


class DoctorProfile(models.Model):
    """
    Профиль врача — дополнительные данные, связанные с User(role=DOCTOR).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        verbose_name='Пользователь',
    )
    specialty = models.ForeignKey(
        'appointments.Specialty',
        on_delete=models.PROTECT,
        verbose_name='Специальность',
    )
    bio = models.TextField(blank=True, verbose_name='О враче')
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Стаж (лет)',
    )
    photo = models.ImageField(
        upload_to='doctors/',
        blank=True,
        null=True,
        verbose_name='Фото',
    )
    is_active = models.BooleanField(default=True, verbose_name='Принимает пациентов')

    class Meta:
        verbose_name = 'Профиль врача'
        verbose_name_plural = 'Профили врачей'

    def __str__(self):
        return f'Д-р {self.user.full_name} — {self.specialty.name}'
