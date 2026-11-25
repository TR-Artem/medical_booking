"""Тесты входа по e-mail, сброса пароля и rate limit."""

import re

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="patient_auth",
            email="Patient@Example.ru",
            password="StrongPass123!",
            first_name="Иван",
            role=User.Role.PATIENT,
        )

    def tearDown(self):
        cache.clear()

    def test_login_by_username(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "patient_auth", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 302)

    def test_login_by_email_ignores_case(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "patient@example.ru", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_external_next_is_ignored(self):
        response = self.client.post(
            reverse("accounts:login") + "?next=https://evil.example/",
            {"username": "patient_auth", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("evil.example", response.url)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "patient_auth", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rate_limit_blocks_after_five_failures(self):
        for _ in range(5):
            self.client.post(
                reverse("accounts:login"),
                {"username": "patient_auth", "password": "wrong"},
            )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "patient_auth", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_full_flow(self):
        response = self.client.post(
            reverse("accounts:password_reset"), {"email": "patient@example.ru"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r"http://testserver(/accounts/reset/[^\s]+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        reset_path = match.group(1)

        response = self.client.get(reset_path)
        self.assertEqual(response.status_code, 302)
        confirm_path = response.url
        response = self.client.get(confirm_path)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            confirm_path,
            {"new_password1": "NewStrongPass456!", "new_password2": "NewStrongPass456!"},
        )
        self.assertEqual(response.status_code, 302)

        self.client.logout()
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "patient@example.ru", "password": "NewStrongPass456!"},
        )
        self.assertEqual(response.status_code, 302)


class RegistrationTest(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(
            username="existing",
            email="taken@example.ru",
            password="StrongPass123!",
        )

    def test_duplicate_email_rejected(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new_user",
                "email": "TAKEN@example.ru",
                "first_name": "Пётр",
                "last_name": "Новый",
                "phone": "",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "pd_consent": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="new_user").exists())
        self.assertContains(response, "уже зарегистрирован")
