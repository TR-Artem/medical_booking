from django.contrib import admin
from .models import Specialty, Room, Schedule, TimeSlot, Appointment


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'floor', 'is_active')
    list_editable = ('is_active',)


class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 0
    readonly_fields = ('start_time', 'end_time', 'is_booked', 'is_blocked')
    can_delete = False


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor_profile', 'date', 'start_time', 'end_time', 'slot_duration', 'room')
    list_filter = ('date', 'doctor_profile__specialty')
    search_fields = ('doctor_profile__user__last_name',)
    inlines = [TimeSlotInline]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor_profile', 'date', 'start_time', 'end_time', 'room', 'is_booked', 'is_blocked')
    list_filter = ('date', 'is_booked', 'is_blocked')
    search_fields = ('doctor_profile__user__last_name',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'slot', 'status', 'created_at')
    list_filter = ('status', 'slot__date')
    search_fields = ('patient__last_name', 'slot__doctor_profile__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'slot__date'
