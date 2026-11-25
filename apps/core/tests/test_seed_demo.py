"""Тесты команды seed_demo."""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import DoctorProfile, User
from apps.appointments.models import Appointment, Room, Schedule, Specialty, TimeSlot


class SeedDemoCommandTest(TestCase):
    def _seed(self, **options):
        call_command("seed_demo", stdout=StringIO(), stderr=StringIO(), **options)

    def test_creates_users_and_profiles(self):
        self._seed()

        self.assertEqual(User.objects.filter(role=User.Role.ADMIN).count(), 1)
        self.assertEqual(User.objects.filter(role=User.Role.SYSADMIN).count(), 1)
        self.assertEqual(User.objects.filter(role=User.Role.DOCTOR).count(), 5)
        self.assertEqual(User.objects.filter(role=User.Role.PATIENT).count(), 1)

        admin = User.objects.get(username="admin@test.ru")
        self.assertFalse(admin.is_superuser)
        self.assertFalse(admin.is_staff)

        sysadmin = User.objects.get(username="sysadmin@test.ru")
        self.assertTrue(sysadmin.is_superuser)
        self.assertTrue(sysadmin.is_staff)
        self.assertTrue(sysadmin.check_password("Test1234!"))

        doctor = User.objects.get(username="doctor@test.ru")
        self.assertEqual(doctor.role, User.Role.DOCTOR)
        self.assertTrue(hasattr(doctor, "doctor_profile"))
        self.assertTrue(doctor.check_password("Test1234!"))

        patient = User.objects.get(username="patient@test.ru")
        self.assertTrue(patient.check_password("Test1234!"))
        self.assertTrue(patient.pd_consent)
        self.assertTrue(patient.phone)

        self.assertEqual(DoctorProfile.objects.count(), 5)
        self.assertEqual(Specialty.objects.count(), 6)
        self.assertEqual(Room.objects.count(), 6)

    def test_creates_schedule_and_slots_for_seven_days(self):
        self._seed()
        today = timezone.localdate()

        self.assertEqual(Schedule.objects.count(), 5 * 7)
        self.assertTrue(Schedule.objects.filter(date=today).exists())
        self.assertTrue(Schedule.objects.filter(date=today + timedelta(days=6)).exists())
        self.assertFalse(Schedule.objects.filter(date=today + timedelta(days=7)).exists())

        doctor = DoctorProfile.objects.get(user__username="doctor@test.ru")
        slots = TimeSlot.objects.filter(doctor_profile=doctor, date=today)
        self.assertGreater(slots.filter(is_booked=False).count(), 0)
        # Обеденный перерыв заблокирован, а не удалён.
        self.assertTrue(slots.filter(is_blocked=True).exists())

    def test_demo_appointments_created_once(self):
        self._seed()
        first_count = Appointment.objects.count()
        self.assertEqual(first_count, 3)

        # Повторный запуск не должен создавать дубликаты.
        self._seed()
        self.assertEqual(Appointment.objects.count(), first_count)
        self.assertEqual(User.objects.filter(role=User.Role.DOCTOR).count(), 5)
        self.assertEqual(Schedule.objects.count(), 5 * 7)

    def test_days_option(self):
        self._seed(days=3)
        self.assertEqual(Schedule.objects.count(), 5 * 3)

    def test_custom_password(self):
        self._seed(password="NewDemo123!")
        doctor = User.objects.get(username="doctor@test.ru")
        self.assertTrue(doctor.check_password("NewDemo123!"))

    def test_legacy_demo_users_removed(self):
        User.objects.create_user(
            username="doctor",
            email="doctor@medcenter.local",
            password="Demo1234!",
            role=User.Role.DOCTOR,
        )
        self._seed()
        self.assertFalse(User.objects.filter(email="doctor@medcenter.local").exists())
        self.assertEqual(DoctorProfile.objects.count(), 5)

    def test_past_demo_appointments_become_completed(self):
        self._seed()
        appointment = Appointment.objects.order_by("slot__date").first()
        appointment.slot.date = timezone.localdate() - timedelta(days=1)
        appointment.slot.save(update_fields=["date"])

        self._seed()

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)
        self.assertEqual(Appointment.objects.count(), 4)
