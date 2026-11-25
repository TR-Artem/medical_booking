"""
Команда наполнения демо-стенда.

Создаёт полный набор данных для показа проекта:
  * администратора клиники;
  * 5 врачей с профилями и специальностями;
  * пациента;
  * расписание всех врачей на 7 дней вперёд со свободными слотами;
  * несколько демонстрационных записей пациента.

Команда идемпотентна: повторный запуск обновляет демо-данные, не создавая
дубликатов. Пароли демо-учёток сбрасываются на указанный (по умолчанию
Test1234!), чтобы вход по логинам из README работал всегда.

Примеры:
    python manage.py seed_demo
    python manage.py seed_demo --days 14
    python manage.py seed_demo --password 'ДругойПароль1!'
"""

from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import DoctorProfile, User
from apps.appointments.models import Appointment, Room, Schedule, Specialty, TimeSlot

DEMO_PASSWORD = "Test1234!"

# Специальности из fixtures/initial_data.json. Команда создаёт их сама,
# чтобы seed_demo работал на пустой базе без отдельного loaddata.
SPECIALTIES = [
    (
        "Кардиология",
        "Диагностика и лечение заболеваний сердечно-сосудистой системы",
        "bi-heart-pulse",
    ),
    ("Терапия", "Первичная медицинская помощь и общая терапия", "bi-clipboard2-pulse"),
    ("Неврология", "Диагностика и лечение заболеваний нервной системы", "bi-activity"),
    ("Офтальмология", "Диагностика и лечение заболеваний органов зрения", "bi-eye"),
    ("Хирургия", "Оперативное и консервативное лечение хирургических заболеваний", "bi-scissors"),
    (
        "Ортопедия",
        "Лечение заболеваний опорно-двигательного аппарата",
        "bi-person-walking",
    ),
]

# Кабинеты: четыре из fixtures + два профильных для хирургии и ортопедии.
ROOMS = [
    ("101", "Кардиология", 1),
    ("102", "Терапия", 1),
    ("201", "Неврология", 2),
    ("202", "Офтальмология", 2),
    ("203", "Хирургия", 2),
    ("204", "Ортопедия", 2),
]

# username, email, first_name, last_name, специальность, стаж, начало, конец, кабинет
DOCTORS = [
    (
        "doctor@test.ru",
        "doctor@test.ru",
        "Анна",
        "Иванова",
        "Кардиология",
        14,
        time(9, 0),
        time(17, 0),
        "101",
    ),
    (
        "doctor2@test.ru",
        "doctor2@test.ru",
        "Пётр",
        "Смирнов",
        "Неврология",
        11,
        time(10, 0),
        time(18, 0),
        "201",
    ),
    (
        "doctor3@test.ru",
        "doctor3@test.ru",
        "Мария",
        "Кузнецова",
        "Терапия",
        8,
        time(8, 0),
        time(16, 0),
        "102",
    ),
    (
        "doctor4@test.ru",
        "doctor4@test.ru",
        "Дмитрий",
        "Соколов",
        "Офтальмология",
        16,
        time(9, 0),
        time(18, 0),
        "202",
    ),
    (
        "doctor5@test.ru",
        "doctor5@test.ru",
        "Елена",
        "Морозова",
        "Хирургия",
        19,
        time(11, 0),
        time(19, 0),
        "203",
    ),
]

DOCTOR_BIOS = {
    "Кардиология": "Кардиолог. Ведёт пациентов с гипертонией, аритмией и ИБС, проводит профилактические осмотры.",
    "Неврология": "Невролог. Диагностика головных болей, нарушений сна, боли в спине и сосудистых заболеваний.",
    "Терапия": "Терапевт. Первичный приём, расшифровка анализов, лечение ОРВИ и хронических заболеваний.",
    "Офтальмология": "Офтальмолог. Проверка зрения, подбор очков, лечение воспалительных заболеваний глаз.",
    "Хирургия": "Хирург. Консультации, малые амбулаторные операции, наблюдение после вмешательств.",
}

ADMIN_LOGIN = "admin@test.ru"
SYSADMIN_LOGIN = "sysadmin@test.ru"
PATIENT_LOGIN = "patient@test.ru"
PATIENT_FIO = ("Иван", "Петров")


class Command(BaseCommand):
    help = "Создаёт демо-данные: администратора, 5 врачей, пациента, расписание на 7 дней"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="На сколько дней вперёд создать расписание (по умолчанию 7)",
        )
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help=f"Пароль демо-учёток (по умолчанию {DEMO_PASSWORD})",
        )
        parser.add_argument(
            "--without-appointments",
            action="store_true",
            help="Не создавать демонстрационные записи пациента",
        )
        parser.add_argument(
            "--keep-legacy",
            action="store_true",
            help="Не удалять старые демо-учётки @medcenter.local от create_demo_data",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        days = options["days"]
        password = options["password"]
        with_appointments = not options["without_appointments"]

        if days < 1:
            self.stderr.write(self.style.ERROR("--days должно быть больше нуля"))
            return

        if not options["keep_legacy"]:
            self._cleanup_legacy_demo()

        specialties = self._seed_specialties()
        rooms = self._seed_rooms()
        admin = self._seed_admin(password)
        sysadmin = self._seed_sysadmin(password)
        doctors = self._seed_doctors(specialties, password)
        patient = self._seed_patient(password)
        schedules = self._seed_schedules(doctors, rooms, days)

        appointments_count = 0
        if with_appointments:
            appointments_count = self._seed_appointments(patient, doctors)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Демо-стенд готов"))
        self.stdout.write(f"  специальностей: {len(specialties)}")
        self.stdout.write(f"  кабинетов:      {len(rooms)}")
        self.stdout.write(f"  врачей:         {len(doctors)}")
        self.stdout.write(f"  расписаний:     {schedules} (на {days} дн.)")
        self.stdout.write(
            f"  слотов:         {TimeSlot.objects.filter(date__gte=timezone.localdate()).count()}"
        )
        self.stdout.write(f"  демо-записей:   {appointments_count}")
        self.stdout.write("")
        self.stdout.write("Вход в систему (пароль у всех учёток одинаковый):")
        self.stdout.write(f"  администратор  {admin.username} / {password}")
        self.stdout.write(f"  сисадмин       {sysadmin.username} / {password}")
        self.stdout.write(f"  врач           {doctors[0][0].username} / {password}")
        self.stdout.write(f"  пациент        {patient.username} / {password}")
        self.stdout.write(f"  остальные врачи: {', '.join(d[0].username for d in doctors[1:])}")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING("Пароли демо-учёток сброшены. Не используйте на проде.")
        )

    # ── справочники ──────────────────────────────────────────────────────────

    def _cleanup_legacy_demo(self):
        """Удаляет учётки старой команды create_demo_data (email @medcenter.local).

        Без этого на стенде остаются дубли врачей: doctor@medcenter.local и
        doctor@test.ru — оба с профилями. Удаляем только явно демонстрационные
        аккаунты, созданные прежней командой.
        """
        legacy = User.objects.filter(email__endswith="@medcenter.local")
        count = legacy.count()
        if count:
            legacy.delete()
            self.stdout.write(f"удалены старые демо-учётки create_demo_data: {count}")

    def _seed_specialties(self):
        result = []
        for name, description, icon in SPECIALTIES:
            specialty, created = Specialty.objects.get_or_create(
                name=name,
                defaults={"description": description, "icon": icon, "is_active": True},
            )
            if created:
                self.stdout.write(f"создана специальность: {name}")
            result.append(specialty)
        return result

    def _seed_rooms(self):
        result = []
        for number, name, floor in ROOMS:
            room, created = Room.objects.get_or_create(
                number=number,
                defaults={"name": name, "floor": floor, "is_active": True},
            )
            if created:
                self.stdout.write(f"создан кабинет: {number} ({name})")
            result.append(room)
        return result

    # ── пользователи ─────────────────────────────────────────────────────────

    def _upsert_user(self, username, email, role, first_name, last_name, password):
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
        user.email = email
        user.role = role
        user.first_name = first_name
        user.last_name = last_name
        user.pd_consent = True
        user.is_active = True
        # Полный доступ к Django admin — только у системного администратора.
        # Администратор клиники работает в приложении и не является суперпользователем.
        user.is_staff = role == User.Role.SYSADMIN
        user.is_superuser = role == User.Role.SYSADMIN
        user.set_password(password)
        user.save()
        self.stdout.write(f"{'создан' if created else 'обновлён'}: {username} ({role})")
        return user

    def _seed_admin(self, password):
        return self._upsert_user(
            ADMIN_LOGIN,
            ADMIN_LOGIN,
            User.Role.ADMIN,
            "Ольга",
            "Хитёва",
            password,
        )

    def _seed_sysadmin(self, password):
        return self._upsert_user(
            SYSADMIN_LOGIN,
            SYSADMIN_LOGIN,
            User.Role.SYSADMIN,
            "Сергей",
            "Системный",
            password,
        )

    def _seed_patient(self, password):
        patient = self._upsert_user(
            PATIENT_LOGIN,
            PATIENT_LOGIN,
            User.Role.PATIENT,
            PATIENT_FIO[0],
            PATIENT_FIO[1],
            password,
        )
        patient.phone = "+7 (999) 123-45-67"
        patient.save(update_fields=["phone"])
        return patient

    def _seed_doctors(self, specialties, password):
        by_name = {s.name: s for s in specialties}
        result = []
        for username, email, first_name, last_name, specialty_name, experience, _, _, _ in DOCTORS:
            user = self._upsert_user(
                username,
                email,
                User.Role.DOCTOR,
                first_name,
                last_name,
                password,
            )
            specialty = by_name.get(specialty_name)
            if specialty is None:
                self.stderr.write(self.style.ERROR(f"Нет специальности {specialty_name}"))
                continue
            profile, _ = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={"specialty": specialty},
            )
            profile.specialty = specialty
            profile.bio = DOCTOR_BIOS.get(specialty_name, "")
            profile.experience_years = experience
            profile.is_active = True
            profile.save()
            result.append((user, profile, specialty_name))
        return result

    # ── расписание ───────────────────────────────────────────────────────────

    def _seed_schedules(self, doctors, rooms, days):
        rooms_by_number = {r.number: r for r in rooms}
        by_specialty = {name: profile for _, profile, name in doctors}
        today = timezone.localdate()
        created = 0

        for _, _, specialty_name in doctors:
            profile = by_specialty[specialty_name]
            config = next(d for d in DOCTORS if d[4] == specialty_name)
            start, end, room_number = config[6], config[7], config[8]
            room = rooms_by_number.get(room_number)

            for offset in range(days):
                day = today + timedelta(days=offset)
                # Воскресенье — короткий день, остальные дни по графику врача.
                day_start, day_end = start, end
                if day.weekday() == 6:
                    day_start, day_end = time(9, 0), time(14, 0)

                schedule, was_created = Schedule.objects.update_or_create(
                    doctor_profile=profile,
                    date=day,
                    defaults={
                        "room": room,
                        "start_time": day_start,
                        "end_time": day_end,
                        "slot_duration": 30,
                    },
                )
                # save() генерирует свободные слоты и не трогает занятые.
                schedule.save()
                self._block_lunch(schedule, day_start, day_end)
                if was_created:
                    created += 1

        return Schedule.objects.filter(
            date__gte=today, date__lt=today + timedelta(days=days)
        ).count()

    def _block_lunch(self, schedule, start, end):
        """Блокирует обеденный перерыв: 4-й час работы (или 13:00, если он в графике)."""
        day = schedule.date
        lunch_start = datetime.combine(day, start) + timedelta(hours=4)
        lunch_end = lunch_start + timedelta(hours=1)
        if lunch_start.time() < end and lunch_end.time() <= end:
            schedule.slots.filter(
                start_time__gte=lunch_start.time(),
                start_time__lt=lunch_end.time(),
            ).update(is_blocked=True)

    # ── демонстрационные записи ──────────────────────────────────────────────

    def _pick_future_slot(self, profile, day, preferred_time):
        """Ближайший свободный слот начиная с желаемого времени.

        Если на выбранный день будущих слотов не осталось (например, демо
        запускают поздно вечером), берём первый свободный слот врача вперёд:
        запись в прошлом создавать нельзя.
        """
        now = timezone.localtime()
        future = TimeSlot.objects.filter(
            doctor_profile=profile,
            is_booked=False,
            is_blocked=False,
        ).filter(Q(date__gt=now.date()) | Q(date=now.date(), start_time__gt=now.time()))

        slot = (
            future.filter(date=day, start_time__gte=preferred_time).order_by("start_time").first()
        )
        if slot is None:
            slot = future.filter(date=day).order_by("start_time").first()
        if slot is None:
            slot = future.order_by("date", "start_time").first()
        return slot

    def _seed_appointments(self, patient, doctors):
        today = timezone.localdate()

        # Демо-стенд может жить несколько дней: вчерашние записи помечаем
        # завершёнными, чтобы они не висели в «предстоящих».
        stale = Appointment.objects.filter(
            patient=patient,
            slot__date__lt=today,
            status__in=[Appointment.Status.BOOKED, Appointment.Status.CONFIRMED],
        )
        stale_count = stale.count()
        if stale_count:
            stale.update(status=Appointment.Status.COMPLETED)
            self.stdout.write(f"завершены прошедшие демо-записи: {stale_count}")

        # seed_demo — это сброс демо-данных: активные записи демо-пациента
        # пересоздаются, чтобы после повторного запуска их было ровно три,
        # а не накапливались с прошлых дней.
        active = Appointment.objects.filter(patient=patient, slot__date__gte=today).exclude(
            status__in=[Appointment.Status.CANCELLED, Appointment.Status.COMPLETED]
        )
        active_count = active.count()
        for appointment in active.select_related("slot"):
            slot = appointment.slot
            slot.is_booked = False
            slot.save(update_fields=["is_booked"])
            appointment.delete()
        if active_count:
            self.stdout.write(f"пересозданы активные демо-записи: {active_count}")

        # По одной записи к первым трём врачам: сегодня, завтра и через два дня.
        plan = [
            (doctors[0][1], today, time(10, 0), "Плановый осмотр, повышенное давление."),
            (
                doctors[1][1],
                today + timedelta(days=1),
                time(11, 0),
                "Головные боли, нарушение сна.",
            ),
            (
                doctors[2][1],
                today + timedelta(days=2),
                time(9, 30),
                "Профилактический приём, ОРВИ.",
            ),
        ]
        created_count = 0

        for profile, day, preferred_time, complaint in plan:
            # Повторный запуск не должен плодить новые записи тому же пациенту.
            if (
                Appointment.objects.filter(
                    patient=patient,
                    slot__doctor_profile=profile,
                    slot__date=day,
                )
                .exclude(status=Appointment.Status.CANCELLED)
                .exists()
            ):
                created_count += 1
                continue

            slot = self._pick_future_slot(profile, day, preferred_time)
            if slot is None:
                continue

            slot.is_booked = True
            slot.save(update_fields=["is_booked"])
            Appointment.objects.create(
                patient=patient,
                slot=slot,
                complaint=complaint,
                status=Appointment.Status.BOOKED,
            )
            self.stdout.write(f"создана запись: {patient.username} → {slot}")
            created_count += 1

        return created_count
