"""Сервисные функции расписания: генерация временны́х слотов."""

from datetime import datetime, timedelta

from .models import TimeSlot


def generate_slots(schedule):
    """Пересобирает свободные слоты расписания, не трогая занятые."""
    # Удаляем только свободные слоты (занятые и заблокированные не трогаем).
    schedule.slots.filter(is_booked=False).delete()

    slot_date = schedule.date
    slot_start = schedule.start_time
    slot_end = schedule.end_time

    if isinstance(slot_date, str):
        from datetime import date as date_type

        slot_date = date_type.fromisoformat(slot_date)
    if isinstance(slot_start, str):
        from datetime import time as time_type

        h, m = slot_start.split(":")[:2]
        slot_start = time_type(int(h), int(m))
    if isinstance(slot_end, str):
        from datetime import time as time_type

        h, m = slot_end.split(":")[:2]
        slot_end = time_type(int(h), int(m))

    start = datetime.combine(slot_date, slot_start)
    end = datetime.combine(slot_date, slot_end)
    delta = timedelta(minutes=schedule.slot_duration)

    current = start
    slots_to_create = []
    while current + delta <= end:
        if not schedule.slots.filter(start_time=current.time()).exists():
            slots_to_create.append(
                TimeSlot(
                    schedule=schedule,
                    doctor_profile=schedule.doctor_profile,
                    date=schedule.date,
                    start_time=current.time(),
                    end_time=(current + delta).time(),
                    room=schedule.room,
                )
            )
        current += delta

    TimeSlot.objects.bulk_create(slots_to_create)
