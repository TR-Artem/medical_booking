# Онлайн-запись в медицинский центр


## Структура проекта


```
medical_booking/                     ← корень проекта
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
│
├── medical_booking/                 ← настройки Django
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── accounts/                    ← регистрация, авторизация, роли
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── appointments/                ← запись, расписание, кабинеты
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── notifications/               ← e-mail уведомления
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   └── services.py
│   │
│   └── core/                        ← главная страница, общие утилиты
│       ├── __init__.py
│       ├── apps.py
│       ├── urls.py
│       └── views.py
│
├── templates/
│   ├── base.html                    ← базовый шаблон
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── profile.html
│   ├── appointments/
│   │   ├── doctor_list.html
│   │   ├── slot_list.html
│   │   ├── appointment_confirm.html
│   │   └── my_appointments.html
│   ├── doctor/
│   │   ├── dashboard.html
│   │   └── schedule.html
│   └── admin_panel/
│       ├── dashboard.html
│       ├── schedule_manage.html
│       └── rooms_manage.html
│
├── static/
│   ├── css/
│   │   └── main.css
│   └── js/
│       └── main.js
│
└── fixtures/
   └── initial_data.json            ← специальности, тестовые врачи
```


## Быстрый старт


```bash
# 1. Клонировать / распаковать проект
cd medical_booking


# 2. Скопировать .env
cp .env.example .env
# Заполнить переменные в .env


# 3. Запустить через Docker
docker-compose up --build


# 4. Выполнить миграции и загрузить тестовые данные
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata fixtures/initial_data.json
docker-compose exec web python manage.py createsuperuser


# 5. Открыть браузер
# http://localhost:8000
```


## Роли пользователей


| Роль | Логин (тест) | Пароль |
|------|-------------|--------|
| Пациент | patient@test.ru | Test1234! |
| Врач | doctor@test.ru | Test1234! |
| Администратор | admin@test.ru | Test1234! |


## Технологический стек
- **Backend**: Python 3.12 + Django 5.x + Django REST Framework
- **Database**: PostgreSQL 16
- **Frontend**: HTML5 + Bootstrap 5 + Vanilla JS
- **Auth**: JWT (djangorestframework-simplejwt)
- **Email**: SMTP / SendGrid
- **Deploy**: Nginx + Gunicorn + Docker



