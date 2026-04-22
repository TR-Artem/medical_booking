"""
Главные URL-маршруты проекта онлайн-записи в медицинский центр.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Административная панель Django
    path('django-admin/', admin.site.urls),

    # Главная страница и общие маршруты
    path('', include('apps.core.urls')),

    # Авторизация, регистрация, профили
    path('accounts/', include('apps.accounts.urls')),

    # Запись к врачу
    path('appointments/', include('apps.appointments.urls')),
]

# Медиа файлы в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
