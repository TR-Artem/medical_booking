"""
Модульные тесты для модели User.
apps/accounts/tests/__init__.py
"""
from django.test import TestCase
from django.db import IntegrityError
from apps.accounts.models import User, DoctorProfile
from apps.appointments.models import Specialty


class UserModelTest(TestCase):
    """Тесты для модели User."""

    def test_create_user_with_required_fields(self):
        """Создание пользователя только с обязательными полями."""
        user = User.objects.create_user(
            username='testuser1',
            email='test1@mail.ru',
            password='password123'
        )
        self.assertEqual(user.username, 'testuser1')
        self.assertEqual(user.email, 'test1@mail.ru')
        self.assertTrue(user.check_password('password123'))

    def test_create_user_with_all_fields(self):
        """Создание пользователя со всеми полями."""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@mail.ru',
            password='password123',
            first_name='Иван',
            last_name='Петров',
            phone='+7 999 123-45-67'
        )
        self.assertEqual(user.first_name, 'Иван')
        self.assertEqual(user.last_name, 'Петров')
        self.assertEqual(user.phone, '+7 999 123-45-67')

    def test_default_role_is_patient(self):
        """Роль по умолчанию — пациент."""
        user = User.objects.create_user(
            username='patient_default',
            email='patient@mail.ru',
            password='password123'
        )
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(user.is_patient)
        self.assertFalse(user.is_doctor)
        self.assertFalse(user.is_clinic_admin)
        self.assertFalse(user.is_sysadmin)

    def test_create_doctor_role(self):
        """Создание пользователя с ролью врача."""
        user = User.objects.create_user(
            username='doctor1',
            email='doctor@mail.ru',
            password='password123',
            role=User.Role.DOCTOR
        )
        self.assertEqual(user.role, User.Role.DOCTOR)
        self.assertTrue(user.is_doctor)
        self.assertFalse(user.is_patient)

    def test_create_admin_role(self):
        """Создание пользователя с ролью администратора."""
        user = User.objects.create_user(
            username='admin1',
            email='admin@mail.ru',
            password='password123',
            role=User.Role.ADMIN
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_clinic_admin)
        self.assertFalse(user.is_doctor)

    def test_create_sysadmin_role(self):
        """Создание пользователя с ролью сисадмина."""
        user = User.objects.create_user(
            username='sysadmin1',
            email='sysadmin@mail.ru',
            password='password123',
            role=User.Role.SYSADMIN
        )
        self.assertEqual(user.role, User.Role.SYSADMIN)
        self.assertTrue(user.is_sysadmin)

    def test_unique_username(self):
        """Username должен быть уникальным."""
        User.objects.create_user(
            username='unique_user',
            email='unique1@mail.ru',
            password='password123'
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='unique_user',
                email='unique2@mail.ru',
                password='password123'
            )

    def test_full_name_with_first_and_last(self):
        """Свойство full_name возвращает имя и фамилию."""
        user = User.objects.create_user(
            username='fullname',
            email='full@mail.ru',
            password='password123',
            first_name='Пётр',
            last_name='Сидоров'
        )
        self.assertEqual(user.full_name, 'Пётр Сидоров')

    def test_full_name_only_first(self):
        """Свойство full_name с только именем."""
        user = User.objects.create_user(
            username='firstonly',
            email='first@mail.ru',
            password='password123',
            first_name='Анна'
        )
        self.assertEqual(user.full_name, 'Анна')

    def test_full_name_without_names(self):
        """Свойство full_name возвращает username если нет имени."""
        user = User.objects.create_user(
            username='no_name_user',
            email='noname@mail.ru',
            password='password123'
        )
        self.assertEqual(user.full_name, 'no_name_user')

    def test_str_representation_patient(self):
        """Строковое представление для пациента."""
        user = User.objects.create_user(
            username='patient_str',
            email='patient_str@mail.ru',
            password='password123',
            first_name='Иван',
            last_name='Петров',
            role=User.Role.PATIENT
        )
        self.assertIn('Иван', str(user))
        self.assertIn('Петров', str(user))
        self.assertIn('Пациент', str(user))

    def test_str_representation_doctor(self):
        """Строковое представление для врача."""
        user = User.objects.create_user(
            username='doctor_str',
            email='doctor_str@mail.ru',
            password='password123',
            first_name='Анна',
            last_name='Смирнова',
            role=User.Role.DOCTOR
        )
        self.assertIn('Анна', str(user))
        self.assertIn('Смирнова', str(user))
        self.assertIn('Врач', str(user))

    def test_is_active_default(self):
        """Пользователь активен по умолчанию."""
        user = User.objects.create_user(
            username='active_test',
            email='active@mail.ru',
            password='password123'
        )
        self.assertTrue(user.is_active)

    def test_deactivate_user(self):
        """Деактивация пользователя."""
        user = User.objects.create_user(
            username='deactive_test',
            email='deactive@mail.ru',
            password='password123'
        )
        user.is_active = False
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_pd_consent_default_false(self):
        """Согласие на обработку ПДн по умолчанию False."""
        user = User.objects.create_user(
            username='consent_test',
            email='consent@mail.ru',
            password='password123'
        )
        self.assertFalse(user.pd_consent)

    def test_pd_consent_true(self):
        """Согласие на обработку ПДн = True."""
        user = User.objects.create_user(
            username='consent_true',
            email='consent_true@mail.ru',
            password='password123',
            pd_consent=True
        )
        self.assertTrue(user.pd_consent)

    def test_get_role_display(self):
        """Метод get_role_display возвращает человеческое название роли."""
        user = User.objects.create_user(
            username='display_role',
            email='display@mail.ru',
            password='password123',
            role=User.Role.PATIENT
        )
        self.assertEqual(user.get_role_display(), 'Пациент')

    def test_check_password(self):
        """Проверка пароля через check_password."""
        user = User.objects.create_user(
            username='check_pass',
            email='check@mail.ru',
            password='secret_password'
        )
        self.assertTrue(user.check_password('secret_password'))
        self.assertFalse(user.check_password('wrong_password'))

    def test_set_password(self):
        """Изменение пароля через set_password."""
        user = User.objects.create_user(
            username='set_pass',
            email='set@mail.ru',
            password='old_password'
        )
        user.set_password('new_password')
        user.save()
        self.assertTrue(user.check_password('new_password'))
        self.assertFalse(user.check_password('old_password'))

    def test_create_user_without_username(self):
        """Создание без username вызывает ошибку."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='',
                email='no_username@mail.ru',
                password='password123'
            )


class DoctorProfileModelTest(TestCase):
    """Тесты модели DoctorProfile."""

    def setUp(self):
        """Создание данных для тестов."""
        self.specialty = Specialty.objects.create(
            name='Терапевт',
            description='Общая терапия',
            is_active=True,
        )

    def test_create_doctor_profile(self):
        """Создание профиля врача."""
        user = User.objects.create_user(
            username='doctor_profile',
            email='doctor_profile@mail.ru',
            password='password123',
            role=User.Role.DOCTOR
        )
        profile = DoctorProfile.objects.create(
            user=user,
            specialty=self.specialty,
            experience_years=10,
            bio='Опытный терапевт',
        )
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.specialty, self.specialty)
        self.assertEqual(profile.experience_years, 10)
        self.assertTrue(profile.is_active)

    def test_doctor_profile_str(self):
        """Строковое представление профиля."""
        user = User.objects.create_user(
            username='doctor_str',
            email='doctor_str@mail.ru',
            password='password123',
            first_name='Иван',
            last_name='Петров',
            role=User.Role.DOCTOR
        )
        profile = DoctorProfile.objects.create(
            user=user,
            specialty=self.specialty,
        )
        self.assertIn('Терапевт', str(profile))

    def test_doctor_profile_default_active(self):
        """Профиль врача активен по умолчанию."""
        user = User.objects.create_user(
            username='doctor_active',
            email='doctor_active@mail.ru',
            password='password123',
            role=User.Role.DOCTOR
        )
        profile = DoctorProfile.objects.create(
            user=user,
            specialty=self.specialty,
        )
        self.assertTrue(profile.is_active)

    def test_doctor_profile_experience_years(self):
        """Проверка поля опыта работы."""
        user = User.objects.create_user(
            username='doctor_exp',
            email='doctor_exp@mail.ru',
            password='password123',
            role=User.Role.DOCTOR
        )
        profile = DoctorProfile.objects.create(
            user=user,
            specialty=self.specialty,
            experience_years=15,
        )
        self.assertEqual(profile.experience_years, 15)

    def test_doctor_profile_one_to_one_relation(self):
        """Один пользователь — один профиль врача."""
        user = User.objects.create_user(
            username='doctor_one',
            email='doctor_one@mail.ru',
            password='password123',
            role=User.Role.DOCTOR
        )
        DoctorProfile.objects.create(
            user=user,
            specialty=self.specialty,
        )
        with self.assertRaises(IntegrityError):
            DoctorProfile.objects.create(
                user=user,
                specialty=self.specialty,
            )
