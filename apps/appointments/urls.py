from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # ── Пациент ────────────────────────────────────────────────────────────
    path('doctors/',                          views.doctor_list,            name='doctor_list'),
    path('doctors/<int:doctor_profile_id>/slots/', views.slot_list,         name='slot_list'),
    path('book/<int:slot_id>/',               views.book_appointment,       name='book'),
    path('my/',                               views.my_appointments,        name='my_appointments'),
    path('cancel/<int:appointment_id>/',      views.cancel_appointment,     name='cancel'),

    # ── Врач ───────────────────────────────────────────────────────────────
    path('doctor/dashboard/',                 views.doctor_dashboard,       name='doctor_dashboard'),
    path('doctor/attendance/<int:appointment_id>/', views.mark_attendance,  name='mark_attendance'),
    path('doctor/block-slot/<int:slot_id>/',  views.block_slot,             name='block_slot'),

    # ── Администратор ──────────────────────────────────────────────────────
    path('admin/dashboard/',                  views.admin_dashboard,        name='admin_dashboard'),
    path('admin/schedule/',                   views.manage_schedule,        name='manage_schedule'),
    path('admin/rooms/',                      views.manage_rooms,           name='manage_rooms'),
    path('admin/cancel/<int:appointment_id>/',views.admin_cancel_appointment, name='admin_cancel'),
]
