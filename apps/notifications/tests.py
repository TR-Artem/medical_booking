"""Тесты напоминаний и периодической задачи Celery Beat."""

from datetime import time, timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from apps.accounts.models import DoctorProfile, User
from apps.appointments.models import Appointment, Room, Schedule, Specialty, TimeSlot
from apps.notifications.tasks import send_appointment_reminders


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ReminderTaskTest(TestCase):
    def setUp(self):
        specialty = Specialty.objects.create(name="Терапия")
        room = Room.objects.create(number="101", name="Терапия")
        doctor = DoctorProfile.objects.create(
            user=User.objects.create_user(
                username="doctor_reminder", password="pass12345", role=User.Role.DOCTOR
            ),
            specialty=specialty,
        )
        self.patient = User.objects.create_user(
            username="patient_reminder",
            email="reminder@example.ru",
            password="pass12345",
            role=User.Role.PATIENT,
        )
        target = timezone.localtime() + timedelta(hours=24)
        schedule = Schedule.objects.create(
            doctor_profile=doctor,
            room=room,
            date=target.date(),
            start_time=time(0, 0),
            end_time=time(0, 30),
            slot_duration=30,
        )
        self.slot = TimeSlot.objects.filter(schedule=schedule).first()
        self.slot.start_time = target.time().replace(second=0, microsecond=0)
        self.slot.end_time = (
            (target + timedelta(minutes=30)).time().replace(second=0, microsecond=0)
        )
        self.slot.save(update_fields=["start_time", "end_time"])
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
        )

    def test_reminder_is_sent_and_marked(self):
        result = send_appointment_reminders()

        self.assertIn("1", result)
        self.assertEqual(len(mail.outbox), 1)
        self.appointment.refresh_from_db()
        self.assertTrue(self.appointment.reminder_sent)

    def test_reminder_is_not_sent_twice(self):
        send_appointment_reminders()
        send_appointment_reminders()
        self.assertEqual(len(mail.outbox), 1)

    def test_periodic_task_is_registered(self):
        self.assertTrue(
            PeriodicTask.objects.filter(
                task="apps.notifications.tasks.send_appointment_reminders",
                enabled=True,
            ).exists()
        )
