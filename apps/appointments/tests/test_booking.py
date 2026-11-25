"""Регрессионные тесты P0: отмена/повторная запись и прошедшие слоты."""

from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import DoctorProfile, User
from apps.appointments.models import Appointment, Room, Schedule, Specialty, TimeSlot

FROZEN_NOW = datetime(2026, 6, 15, 12, 0)


def frozen_time():
    """Возвращает «замороженное» aware-время в часовом поясе клиники."""
    return timezone.make_aware(FROZEN_NOW, timezone.get_current_timezone())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CancelRebookTest(TestCase):
    """После отмены слот должен снова приниматься, история сохраняется."""

    def setUp(self):
        self.specialty = Specialty.objects.create(name="Терапия")
        self.room = Room.objects.create(number="101", name="Терапия")
        self.doctor_user = User.objects.create_user(
            username="doctor_rebook", password="pass12345", role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, specialty=self.specialty)
        self.patient = User.objects.create_user(
            username="patient_rebook", password="pass12345", role=User.Role.PATIENT
        )
        self.other_patient = User.objects.create_user(
            username="patient_other", password="pass12345", role=User.Role.PATIENT
        )
        self.schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            room=self.room,
            date=timezone.localdate() + timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration=30,
        )
        self.slot = TimeSlot.objects.filter(schedule=self.schedule).first()
        self.client.force_login(self.patient)

    def test_patient_can_rebook_after_cancellation(self):
        response = self.client.post(reverse("appointments:book", args=[self.slot.pk]))
        self.assertEqual(response.status_code, 302)
        first = Appointment.objects.get(slot=self.slot)
        self.assertEqual(first.status, Appointment.Status.BOOKED)

        self.client.post(reverse("appointments:cancel", args=[first.pk]))
        first.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(first.status, Appointment.Status.CANCELLED)
        self.assertFalse(self.slot.is_booked)

        response = self.client.post(reverse("appointments:book", args=[self.slot.pk]))
        self.assertEqual(response.status_code, 302)

        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)
        self.assertEqual(Appointment.objects.filter(slot=self.slot).count(), 2)
        active = Appointment.objects.filter(slot=self.slot).exclude(
            status=Appointment.Status.CANCELLED
        )
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().status, Appointment.Status.BOOKED)

    def test_second_active_booking_is_rejected_by_database(self):
        Appointment.objects.create(
            slot=self.slot,
            patient=self.patient,
            status=Appointment.Status.BOOKED,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    slot=self.slot,
                    patient=self.other_patient,
                    status=Appointment.Status.BOOKED,
                )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PastSlotTest(TestCase):
    """Слоты, которые уже начались, нельзя записать и не видно в списке."""

    def setUp(self):
        self.specialty = Specialty.objects.create(name="Хирургия")
        self.room = Room.objects.create(number="202", name="Хирургия")
        self.doctor_user = User.objects.create_user(
            username="doctor_past", password="pass12345", role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, specialty=self.specialty)
        self.patient = User.objects.create_user(
            username="patient_past", password="pass12345", role=User.Role.PATIENT
        )
        self.schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            room=self.room,
            date=FROZEN_NOW.date(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30,
        )
        self.slots = list(TimeSlot.objects.filter(schedule=self.schedule))
        self.past_slot = self.slots[0]  # 09:00, «сейчас» 12:00
        self.future_slot = self.slots[-1]  # 16:30
        self.client.force_login(self.patient)

    def test_is_available_is_false_for_started_slot(self):
        with patch("django.utils.timezone.now", return_value=frozen_time()):
            self.assertFalse(self.past_slot.is_available)
            self.assertTrue(self.future_slot.is_available)

    def test_booking_started_slot_is_rejected(self):
        with patch("django.utils.timezone.now", return_value=frozen_time()):
            response = self.client.post(reverse("appointments:book", args=[self.past_slot.pk]))
        self.assertEqual(response.status_code, 302)
        self.past_slot.refresh_from_db()
        self.assertFalse(self.past_slot.is_booked)
        self.assertFalse(Appointment.objects.exists())

    def test_slot_list_hides_started_slots(self):
        with patch("django.utils.timezone.now", return_value=frozen_time()):
            response = self.client.get(reverse("appointments:slot_list", args=[self.doctor.pk]))
        self.assertEqual(response.status_code, 200)
        grouped = response.context["grouped_slots"]
        times = [slot.start_time for slot in grouped.get(FROZEN_NOW.date(), [])]
        self.assertNotIn(time(9, 0), times)
        self.assertIn(time(12, 30), times)
        self.assertIn(time(16, 30), times)

    def test_booking_future_slot_today_still_works(self):
        with patch("django.utils.timezone.now", return_value=frozen_time()):
            response = self.client.post(reverse("appointments:book", args=[self.future_slot.pk]))
        self.assertEqual(response.status_code, 302)
        self.future_slot.refresh_from_db()
        self.assertTrue(self.future_slot.is_booked)
        self.assertEqual(Appointment.objects.count(), 1)


class SlotDateTest(TestCase):
    """is_available не должен зависеть от UTC-даты контейнера."""

    def test_yesterday_slot_is_unavailable(self):
        specialty = Specialty.objects.create(name="Неврология")
        room = Room.objects.create(number="303", name="Неврология")
        doctor_user = User.objects.create_user(
            username="doctor_date", password="pass12345", role=User.Role.DOCTOR
        )
        doctor = DoctorProfile.objects.create(user=doctor_user, specialty=specialty)
        schedule = Schedule.objects.create(
            doctor_profile=doctor,
            room=room,
            date=timezone.localdate() - timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration=30,
        )
        slot = TimeSlot.objects.filter(schedule=schedule).first()
        self.assertFalse(slot.is_available)
