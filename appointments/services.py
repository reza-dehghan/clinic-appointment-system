from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from appointments.models import Appointment
from doctors.models import DoctorClinic, DoctorSchedule


def generate_schedule_slots(
    doctor_schedule: DoctorSchedule,
    target_date: date,
) -> list[datetime]:
    schedule_start = datetime.combine(target_date, doctor_schedule.start_time)
    schedule_end = datetime.combine(target_date, doctor_schedule.end_time)
    slot_duration = timedelta(minutes=doctor_schedule.slot_duration_minutes)

    slots: list[datetime] = []
    current_start = schedule_start

    while current_start + slot_duration <= schedule_end:
        slots.append(current_start)
        current_start += slot_duration

    return slots


@transaction.atomic
def book_appointment(
    *,
    patient,
    doctor,
    clinic,
    start_time: datetime,
) -> Appointment:
    schedule = (
        DoctorSchedule.objects.select_for_update()
        .filter(
            doctor=doctor,
            clinic=clinic,
            weekday=start_time.weekday(),
            is_active=True,
        )
        .first()
    )

    if schedule is None:
        raise ValidationError("No active schedule found for this doctor and clinic.")

    membership_exists = DoctorClinic.objects.filter(
        doctor=doctor,
        clinic=clinic,
        is_active=True,
    ).exists()
    if not membership_exists:
        raise ValidationError(
            "Doctor does not have an active clinic membership for this booking."
        )

    schedule_start = timezone.make_aware(
        datetime.combine(start_time.date(), schedule.start_time)
    )
    schedule_end = timezone.make_aware(
        datetime.combine(start_time.date(), schedule.end_time)
    )
    slot_duration = timedelta(minutes=schedule.slot_duration_minutes)
    end_time = start_time + slot_duration

    if start_time < schedule_start or end_time > schedule_end:
        raise ValidationError("Requested start time is outside the doctor's schedule.")

    if ((start_time - schedule_start) % slot_duration) != timedelta(0):
        raise ValidationError(
            "Requested start time does not align with the schedule slot duration."
        )

    try:
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            start_time=start_time,
            end_time=end_time,
            status=Appointment.AppointmentStatus.CONFIRMED,
        )
    except IntegrityError as exc:
        raise ValidationError("This appointment slot is already booked.") from exc

    return appointment


@transaction.atomic
def cancel_appointment(*, appointment, cancellation_reason=None):
    if appointment.status in [
        Appointment.AppointmentStatus.CANCELLED,
        Appointment.AppointmentStatus.COMPLETED,
        Appointment.AppointmentStatus.NO_SHOW,
    ]:
        raise ValidationError("Appointment cannot be cancelled")

    appointment.status = Appointment.AppointmentStatus.CANCELLED
    appointment.cancellation_reason = cancellation_reason or ""
    appointment.save(
        update_fields=[
            "status",
            "cancellation_reason",
            "updated_at",
        ]
    )

    return appointment
