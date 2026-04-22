"""
Celery — асинхронные задачи (отправка уведомлений, напоминания).
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_booking.settings')

app = Celery('medical_booking')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
