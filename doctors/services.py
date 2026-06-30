from datetime import time
from typing import TypedDict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from accounts.models import User
from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic, DoctorSchedule, Specialty
from doctors.selectors import doctor_has_active_membership_in_clinic


class DoctorCreateData(TypedDict):
    user_id: int
    medical_license_number: str
    bio: str
    consultation_fee: int | None
    specialties: list[int]


class DoctorClinicCreateData(TypedDict, total=False):
    doctor_id: int
    clinic_id: int
    is_active: bool


class DoctorScheduleCreateData(TypedDict, total=False):
    doctor_id: int
    clinic_id: int
    weekday: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    is_active: bool


@transaction.atomic
def create_doctor(data: DoctorCreateData) -> Doctor:
    user = User.objects.get(id=data["user_id"])

    doctor = Doctor.objects.create(
        user=user,
        medical_license_number=data["medical_license_number"],
        bio=data["bio"],
        consultation_fee=data["consultation_fee"],
    )

    specialties = Specialty.objects.filter(id__in=data["specialties"])
    doctor.specialties.set(specialties)

    return doctor


@transaction.atomic
def update_doctor(doctor: Doctor, data: dict) -> Doctor:
    update_fields: list[str] = []

    for field in ("medical_license_number", "bio", "consultation_fee", "is_active"):
        if field in data:
            setattr(doctor, field, data[field])
            update_fields.append(field)

    if update_fields:
        doctor.save(update_fields=update_fields)

    if "specialties" in data:
        specialties = Specialty.objects.filter(id__in=data["specialties"])
        doctor.specialties.set(specialties)

    return doctor


@transaction.atomic
def deactivate_doctor(doctor: Doctor) -> Doctor:
    doctor.is_active = False
    doctor.save(update_fields=["is_active"])
    return doctor


@transaction.atomic
def create_doctor_clinic(
    *,
    data: DoctorClinicCreateData,
) -> DoctorClinic:
    doctor = Doctor.objects.get(id=data["doctor_id"])
    clinic = Clinic.objects.get(id=data["clinic_id"])

    if DoctorClinic.objects.filter(
        doctor_id=data["doctor_id"],
        clinic_id=data["clinic_id"],
    ).exists():
        raise ValidationError("Doctor is already assigned to this clinic")

    create_kwargs: dict[str, int | bool | Doctor | Clinic] = {
        "doctor": doctor,
        "clinic": clinic,
        "is_active": data.get("is_active", True),
    }

    return DoctorClinic.objects.create(**create_kwargs)


@transaction.atomic
def update_doctor_clinic(
    *,
    doctor_clinic: DoctorClinic,
    is_active: bool | None = None,
) -> DoctorClinic:
    update_fields: list[str] = []

    if is_active is not None and doctor_clinic.is_active != is_active:
        doctor_clinic.is_active = is_active
        update_fields.append("is_active")

    if update_fields:
        doctor_clinic.save(update_fields=update_fields)

    return doctor_clinic


@transaction.atomic
def deactivate_doctor_clinic(
    *,
    doctor_clinic: DoctorClinic,
) -> DoctorClinic:
    doctor_clinic.is_active = False
    doctor_clinic.save(update_fields=["is_active"])
    return doctor_clinic


def _validate_doctor_schedule_data(
    *,
    doctor_id: int,
    clinic_id: int,
    weekday: int,
    start_time: time,
    end_time: time,
    slot_duration_minutes: int,
    is_active: bool,
    exclude_schedule_id: int | None = None,
) -> None:
    if not doctor_has_active_membership_in_clinic(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
    ):
        raise ValidationError("Doctor must have an active clinic membership")

    if start_time >= end_time:
        raise ValidationError("start_time must be earlier than end_time")

    if slot_duration_minutes <= 0:
        raise ValidationError("slot_duration_minutes must be greater than 0")

    if not is_active:
        return

    overlapping_schedules = DoctorSchedule.objects.filter(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        weekday=weekday,
        is_active=True,
    ).filter(
        Q(start_time__lt=end_time) & Q(end_time__gt=start_time),
    )

    if exclude_schedule_id is not None:
        overlapping_schedules = overlapping_schedules.exclude(id=exclude_schedule_id)

    if overlapping_schedules.exists():
        raise ValidationError("Active doctor schedules must not overlap")


@transaction.atomic
def create_doctor_schedule(
    *,
    data: DoctorScheduleCreateData,
) -> DoctorSchedule:
    doctor = Doctor.objects.get(id=data["doctor_id"])
    clinic = Clinic.objects.get(id=data["clinic_id"])
    is_active = data.get("is_active", True)

    _validate_doctor_schedule_data(
        doctor_id=doctor.id,
        clinic_id=clinic.id,
        weekday=data["weekday"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        slot_duration_minutes=data["slot_duration_minutes"],
        is_active=is_active,
    )

    return DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=data["weekday"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        slot_duration_minutes=data["slot_duration_minutes"],
        is_active=is_active,
    )


@transaction.atomic
def update_doctor_schedule(
    *,
    doctor_schedule: DoctorSchedule,
    weekday: int | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
    slot_duration_minutes: int | None = None,
    is_active: bool | None = None,
) -> DoctorSchedule:
    new_weekday = doctor_schedule.weekday if weekday is None else weekday
    new_start_time = doctor_schedule.start_time if start_time is None else start_time
    new_end_time = doctor_schedule.end_time if end_time is None else end_time
    new_slot_duration_minutes = (
        doctor_schedule.slot_duration_minutes
        if slot_duration_minutes is None
        else slot_duration_minutes
    )
    new_is_active = doctor_schedule.is_active if is_active is None else is_active

    _validate_doctor_schedule_data(
        doctor_id=doctor_schedule.doctor_id,
        clinic_id=doctor_schedule.clinic_id,
        weekday=new_weekday,
        start_time=new_start_time,
        end_time=new_end_time,
        slot_duration_minutes=new_slot_duration_minutes,
        is_active=new_is_active,
        exclude_schedule_id=doctor_schedule.id,
    )

    update_fields: list[str] = []

    if doctor_schedule.weekday != new_weekday:
        doctor_schedule.weekday = new_weekday
        update_fields.append("weekday")

    if doctor_schedule.start_time != new_start_time:
        doctor_schedule.start_time = new_start_time
        update_fields.append("start_time")

    if doctor_schedule.end_time != new_end_time:
        doctor_schedule.end_time = new_end_time
        update_fields.append("end_time")

    if doctor_schedule.slot_duration_minutes != new_slot_duration_minutes:
        doctor_schedule.slot_duration_minutes = new_slot_duration_minutes
        update_fields.append("slot_duration_minutes")

    if doctor_schedule.is_active != new_is_active:
        doctor_schedule.is_active = new_is_active
        update_fields.append("is_active")

    if update_fields:
        doctor_schedule.save(update_fields=update_fields)

    return doctor_schedule


@transaction.atomic
def deactivate_doctor_schedule(
    *,
    doctor_schedule: DoctorSchedule,
) -> DoctorSchedule:
    doctor_schedule.is_active = False
    doctor_schedule.save(update_fields=["is_active"])
    return doctor_schedule
