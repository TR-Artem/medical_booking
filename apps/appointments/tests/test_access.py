"""Тесты прав доступа (инцидент BUG-12, этап 6)."""

from datetime import date, time

from django.test import TestCase

from apps.accounts.models import DoctorProfile, User
from apps.appointments.models import Appointment, Room, Schedule, Specialty, TimeSlot


class RoleAccessTest(TestCase):
    """Закрытые разделы должны отдавать 403, а не редирект."""

    def setUp(self):
        self.specialty = Specialty.objects.create(name="Терапия")
        self.room = Room.objects.create(number="501", name="Терапия")
        self.patient = User.objects.create_user(
            username="patient_acl", password="password123", role=User.Role.PATIENT
        )
        self.patient2 = User.objects.create_user(
            username="patient_acl2", password="password123", role=User.Role.PATIENT
        )
        self.doctor_user = User.objects.create_user(
            username="doctor_acl", password="password123", role=User.Role.DOCTOR
        )
        self.admin = User.objects.create_user(
            username="admin_acl", password="password123", role=User.Role.ADMIN
        )
        self.sysadmin = User.objects.create_user(
            username="sysadmin_acl", password="password123", role=User.Role.SYSADMIN
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, specialty=self.specialty)
        self.schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            room=self.room,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration=30,
        )
        self.slot = TimeSlot.objects.filter(schedule=self.schedule).first()

    def test_patient_gets_403_on_admin_dashboard(self):
        self.client.force_login(self.patient)
        response = self.client.get("/appointments/admin/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_patient_gets_403_on_admin_users(self):
        self.client.force_login(self.patient)
        response = self.client.get("/appointments/admin/users/")
        self.assertEqual(response.status_code, 403)

    def test_doctor_gets_403_on_admin_dashboard(self):
        self.client.force_login(self.doctor_user)
        response = self.client.get("/appointments/admin/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_patient_gets_403_on_doctor_dashboard(self):
        self.client.force_login(self.patient)
        response = self.client.get("/appointments/doctor/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_admin_gets_200_on_admin_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get("/appointments/admin/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_sysadmin_gets_200_on_admin_users(self):
        self.client.force_login(self.sysadmin)
        response = self.client.get("/appointments/admin/users/")
        self.assertEqual(response.status_code, 200)

    def test_patient_cannot_cancel_foreign_appointment(self):
        appointment = Appointment.objects.create(slot=self.slot, patient=self.patient)
        self.client.force_login(self.patient2)
        response = self.client.post(f"/appointments/cancel/{appointment.pk}/")
        self.assertEqual(response.status_code, 404)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.BOOKED)
