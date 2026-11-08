"""
Команда создания демонстрационных данных.

Создаёт пользователей всех ролей, профили врачей, расписание на ближайшие
рабочие дни и одну запись пациента. Нужна для демонстрации проекта и для
проверок на этапах тестирования и безопасности.

Пароль по умолчанию — только для локального демо-стенда. Для повторного
запуска с другим паролем: python manage.py create_demo_data --password <пароль>
"""

from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from apps.accounts.models import DoctorProfile, User
from apps.appointments.models import Appointment, Room, Schedule, Specialty, TimeSlot

DEMO_USERS = [
    # username, email, role, first_name, last_name
    ("admin", "admin@medcenter.local", User.Role.ADMIN, "Ольга", "Хитёва"),
    ("sysadmin", "sysadmin@medcenter.local", User.Role.SYSADMIN, "Артём", "Гаврик"),
    ("doctor", "doctor@medcenter.local", User.Role.DOCTOR, "Анна", "Иванова"),
    ("doctor2", "doctor2@medcenter.local", User.Role.DOCTOR, "Пётр", "Смирнов"),
    ("doctor3", "doctor3@medcenter.local", User.Role.DOCTOR, "Мария", "Кузнецова"),
    ("patient", "patient@medcenter.local", User.Role.PATIENT, "Иван", "Петров"),
    ("patient2", "patient2@medcenter.local", User.Role.PATIENT, "Елена", "Соколова"),
]

DOCTOR_SPECIALTIES = {
    "doctor": "Кардиология",
    "doctor2": "Неврология",
    "doctor3": "Терапия",
}

DEMO_PASSWORD = "Demo1234!"


class Command(BaseCommand):
    help = "Создаёт демо-пользователей, врачей, расписание и одну запись"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help="Пароль для демо-пользователей (по умолчанию Demo1234!)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=5,
            help="На сколько рабочих дней вперёд создать расписание",
        )

    def handle(self, *args, **options):
        password = options["password"]
        days = options["days"]

        specialties = {s.name: s for s in Specialty.objects.all()}
        if not specialties:
            self.stderr.write(
                self.style.ERROR("Нет специальностей. Сначала: loaddata initial_data.json")
            )
            return

        users = {}
        for username, email, role, first_name, last_name in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": role,
                    "first_name": first_name,
                    "last_name": last_name,
                    "pd_consent": True,
                },
            )
            user.role = role
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.pd_consent = True
            user.is_staff = role in (User.Role.ADMIN, User.Role.SYSADMIN)
            user.is_superuser = role == User.Role.SYSADMIN
            user.set_password(password)
            user.save()
            users[username] = user
            self.stdout.write(f"{'создан' if created else 'обновлён'}: {username} ({role})")

        rooms = list(Room.objects.filter(is_active=True))
        if not rooms:
            self.stderr.write(
                self.style.ERROR("Нет кабинетов. Сначала: loaddata initial_data.json")
            )
            return

        # Профили врачей
        for username, specialty_name in DOCTOR_SPECIALTIES.items():
            specialty = specialties.get(specialty_name)
            if not specialty:
                self.stderr.write(f"нет специальности {specialty_name}, пропуск")
                continue
            profile, _ = DoctorProfile.objects.get_or_create(
                user=users[username],
                defaults={
                    "specialty": specialty,
                    "bio": f"Врач-{specialty.name.lower()}, ведёт приём в клинике МедЦентр.",
                    "experience_years": 8,
                    "is_active": True,
                },
            )
            profile.specialty = specialty
            profile.is_active = True
            profile.save()

            # Расписание: сегодня и следующие рабочие дни
            for offset in range(days):
                day = date.today() + timedelta(days=offset)
                if day.weekday() >= 5:
                    continue
                schedule, _ = Schedule.objects.get_or_create(
                    doctor_profile=profile,
                    date=day,
                    defaults={
                        "room": rooms[0],
                        "start_time": time(9, 0),
                        "end_time": time(13, 0),
                        "slot_duration": 30,
                    },
                )
                schedule.save()  # генерирует слоты

        # Одна запись пациента на первый свободный слот
        patient = users["patient"]
        slot = (
            TimeSlot.objects.filter(is_booked=False, is_blocked=False, date__gte=date.today())
            .order_by("date", "start_time")
            .first()
        )
        if slot and not Appointment.objects.filter(patient=patient).exists():
            slot.is_booked = True
            slot.save(update_fields=["is_booked"])
            Appointment.objects.create(
                patient=patient,
                slot=slot,
                complaint="Плановый осмотр, повышенное давление.",
            )
            self.stdout.write(f"создана запись: {patient.username} → {slot}")
        else:
            self.stdout.write("запись не создана: нет свободных слотов или уже есть запись")

        self.stdout.write(self.style.SUCCESS(f"Демо-данные готовы. Пароль всех учёток: {password}"))
