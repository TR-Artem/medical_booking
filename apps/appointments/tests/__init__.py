"""
Модульные тесты для моделей приложения appointments.
"""
from django.test import TestCase
from datetime import timedelta, time, date
from apps.accounts.models import User, DoctorProfile
from apps.appointments.models import Specialty, Room, Schedule, TimeSlot, Appointment


class SpecialtyModelTest(TestCase):
    """Тесты модели Specialty."""

    def test_create_specialty(self):
        """Создание специальности."""
        specialty = Specialty.objects.create(
            name='Кардиология',
            description='Болезни сердца',
            is_active=True,
        )
        self.assertEqual(specialty.name, 'Кардиология')
        self.assertTrue(specialty.is_active)
        self.assertEqual(str(specialty), 'Кардиология')

    def test_specialty_unique_name(self):
        """Название специальности должно быть уникальным."""
        Specialty.objects.create(name='Неврология')
        with self.assertRaises(Exception):
            Specialty.objects.create(name='Неврология')


class RoomModelTest(TestCase):
    """Тесты модели Room."""

    def test_create_room(self):
        """Создание кабинета."""
        room = Room.objects.create(
            number='101',
            name='Кардиология',
            floor=1,
            is_active=True,
        )
        self.assertEqual(room.number, '101')
        self.assertEqual(room.floor, 1)
        self.assertTrue(room.is_active)

    def test_room_unique_number(self):
        """Номер кабинета должен быть уникальным."""
        Room.objects.create(number='102', name='Терапия')
        with self.assertRaises(Exception):
            Room.objects.create(number='102', name='Хирургия')


class ScheduleModelTest(TestCase):
    """Тесты модели Schedule."""

    def setUp(self):
        """Создание данных для тестов."""
        self.specialty = Specialty.objects.create(name='Терапевт')
        self.user = User.objects.create_user(
            username='schedule_doctor',
            email='schedule@test.com',
            password='testpass123',
            role=User.Role.DOCTOR,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            specialty=self.specialty,
        )
        self.room = Room.objects.create(number='201', name='Терапия')

    def test_create_schedule(self):
        """Создание расписания."""
        schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            date=date.today() + timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration=30,
            room=self.room,
        )
        self.assertEqual(schedule.doctor_profile, self.doctor)
        self.assertEqual(schedule.slot_duration, 30)

    def test_schedule_auto_generate_slots(self):
        """Автоматическая генерация слотов."""
        future_date = date.today() + timedelta(days=10)
        schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            date=future_date,
            start_time=time(9, 0),
            end_time=time(11, 0),
            slot_duration=30,
            room=self.room,
        )
        slots = TimeSlot.objects.filter(schedule=schedule)
        self.assertEqual(slots.count(), 4)


class TimeSlotModelTest(TestCase):
    """Тесты модели TimeSlot."""

    def setUp(self):
        """Создание данных для тестов."""
        self.specialty = Specialty.objects.create(name='Хирург')
        self.user = User.objects.create_user(
            username='slot_doctor',
            email='slot@test.com',
            password='testpass123',
            role=User.Role.DOCTOR,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            specialty=self.specialty,
        )
        self.room = Room.objects.create(number='301', name='Хирургия')
        # Создаём слот через schedule для генерации
        self.schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            date=date.today() + timedelta(days=30),
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30,
            room=self.room,
        )
        self.slot = TimeSlot.objects.filter(schedule=self.schedule).first()

    def test_slot_available_when_not_booked(self):
        """Слот доступен когда не забронирован."""
        self.assertFalse(self.slot.is_booked)
        self.assertTrue(self.slot.is_available)

    def test_slot_not_available_when_booked(self):
        """Слот недоступен при бронировании."""
        self.slot.is_booked = True
        self.slot.save()
        self.assertFalse(self.slot.is_available)

    def test_slot_not_available_when_blocked(self):
        """Слот недоступен при блокировке."""
        self.slot.is_blocked = True
        self.slot.save()
        self.assertFalse(self.slot.is_available)


class AppointmentModelTest(TestCase):
    """Тесты модели Appointment."""

    def setUp(self):
        """Создание данных для тестов."""
        self.specialty = Specialty.objects.create(name='Офтальмолог')
        self.doctor_user = User.objects.create_user(
            username='appt_doctor',
            email='appt_doctor@test.com',
            password='testpass123',
            role=User.Role.DOCTOR,
        )
        self.patient_user = User.objects.create_user(
            username='appt_patient',
            email='appt_patient@test.com',
            password='testpass123',
            role=User.Role.PATIENT,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty=self.specialty,
        )
        self.room = Room.objects.create(number='401', name='Офтальмология')
        # Используем уникальную дату
        self.schedule = Schedule.objects.create(
            doctor_profile=self.doctor,
            date=date.today() + timedelta(days=40),
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30,
            room=self.room,
        )
        self.slot = TimeSlot.objects.filter(schedule=self.schedule).first()

    def test_create_appointment(self):
        """Создание записи на приём."""
        appointment = Appointment.objects.create(
            slot=self.slot,
            patient=self.patient_user,
            status=Appointment.Status.BOOKED,
        )
        self.assertEqual(appointment.status, Appointment.Status.BOOKED)
        self.assertEqual(appointment.patient, self.patient_user)
        self.assertEqual(appointment.slot, self.slot)

    def test_appointment_cancel(self):
        """Отмена записи освобождает слот."""
        appointment = Appointment.objects.create(
            slot=self.slot,
            patient=self.patient_user,
            status=Appointment.Status.BOOKED,
        )
        appointment.cancel()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)

    def test_appointment_statuses(self):
        """Все статусы записи."""
        appointment = Appointment.objects.create(
            slot=self.slot,
            patient=self.patient_user,
        )
        self.assertEqual(appointment.status, Appointment.Status.BOOKED)

        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)