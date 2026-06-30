from datetime import date, timedelta

from appointments.models import Appointment
from appointments.services import generate_schedule_slots
from doctors.models import DoctorSchedule


def get_available_slots(doctor, clinic, date: date) -> list[dict]:
    schedule = (
        DoctorSchedule.objects.filter(
            doctor=doctor,
            clinic=clinic,
            weekday=date.weekday(),
            is_active=True,
        )
        .order_by("id")
        .first()
    )

    if schedule is None:
        return []

    all_slots = generate_schedule_slots(schedule, date)

    booked_start_times = set(
        Appointment.objects.filter(
            doctor=doctor,
            clinic=clinic,
            start_time__date=date,
        ).values_list("start_time", flat=True)
    )

    slot_duration = timedelta(minutes=schedule.slot_duration_minutes)

    available_slots = [
        {
            "start_time": slot_start,
            "end_time": slot_start + slot_duration,
        }
        for slot_start in all_slots
        if slot_start not in booked_start_times
    ]

    return available_slots


def get_patient_appointments(*, patient):
    return (
        Appointment.objects.filter(patient=patient)
        .select_related("doctor", "clinic")
        .order_by("-start_time")
    )


def get_patient_appointment_by_id(*, appointment_id, patient):
    return Appointment.objects.select_related("doctor", "clinic").get(
        id=appointment_id,
        patient=patient,
    )


def get_patient_active_appointment(*, appointment_id, patient):
    return Appointment.objects.get(
        id=appointment_id,
        patient=patient,
    )
