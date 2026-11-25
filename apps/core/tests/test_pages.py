"""Тесты служебных страниц: health-check, ПДн, 404/500."""

from django.test import TestCase
from django.urls import reverse


class ServicePagesTest(TestCase):
    def test_healthz_ok(self):
        response = self.client.get(reverse("core:healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["db"])
        self.assertIn("version", response.json())

    def test_privacy_page(self):
        response = self.client.get(reverse("core:privacy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Политика обработки персональных данных")

    def test_404_page(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Страница не найдена", status_code=404)
