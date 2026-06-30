from django.db.models import QuerySet

from doctors.models import Doctor, DoctorClinic, DoctorSchedule


def list_doctors() -> QuerySet[Doctor]:
    return Doctor.objects.select_related("user").prefetch_related("specialties")


def get_doctor_by_id(doctor_id: int) -> Doctor:
    return (
        Doctor.objects.select_related("user")
        .prefetch_related("specialties")
        .get(id=doctor_id)
    )


def list_active_doctors() -> QuerySet[Doctor]:
    return (
        Doctor.objects.select_related("user")
        .prefetch_related("specialties")
        .filter(is_active=True)
    )


def _doctor_clinic_base_queryset() -> QuerySet[DoctorClinic]:
    return DoctorClinic.objects.select_related(
        "doctor",
        "doctor__user",
        "clinic",
    )


def list_doctor_clinics(
    *,
    doctor_id: int | None = None,
    clinic_id: int | None = None,
    is_active: bool | None = None,
) -> QuerySet[DoctorClinic]:
    queryset = _doctor_clinic_base_queryset()

    if doctor_id is not None:
        queryset = queryset.filter(doctor_id=doctor_id)

    if clinic_id is not None:
        queryset = queryset.filter(clinic_id=clinic_id)

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset.order_by("-id")


def get_doctor_clinic(
    *,
    doctor_clinic_id: int,
) -> DoctorClinic:
    return _doctor_clinic_base_queryset().get(id=doctor_clinic_id)


def get_doctor_clinic_by_doctor_and_clinic(
    *,
    doctor_id: int,
    clinic_id: int,
) -> DoctorClinic | None:
    return (
        _doctor_clinic_base_queryset()
        .filter(doctor_id=doctor_id, clinic_id=clinic_id)
        .first()
    )


def doctor_has_active_membership_in_clinic(
    *,
    doctor_id: int,
    clinic_id: int,
) -> bool:
    return DoctorClinic.objects.filter(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        is_active=True,
    ).exists()


def _doctor_schedule_base_queryset() -> QuerySet[DoctorSchedule]:
    return DoctorSchedule.objects.select_related(
        "doctor",
        "doctor__user",
        "clinic",
    )


def list_doctor_schedules(
    *,
    doctor_id: int | None = None,
    clinic_id: int | None = None,
    weekday: int | None = None,
    is_active: bool | None = None,
) -> QuerySet[DoctorSchedule]:
    queryset = _doctor_schedule_base_queryset()

    if doctor_id is not None:
        queryset = queryset.filter(doctor_id=doctor_id)

    if clinic_id is not None:
        queryset = queryset.filter(clinic_id=clinic_id)

    if weekday is not None:
        queryset = queryset.filter(weekday=weekday)

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset.order_by("weekday", "start_time", "id")


def get_doctor_schedule(
    *,
    doctor_schedule_id: int,
) -> DoctorSchedule:
    return _doctor_schedule_base_queryset().get(id=doctor_schedule_id)


def list_doctor_schedules_for_doctor(
    *,
    doctor_id: int,
    clinic_id: int | None = None,
    weekday: int | None = None,
    is_active: bool | None = None,
) -> QuerySet[DoctorSchedule]:
    queryset = _doctor_schedule_base_queryset().filter(doctor_id=doctor_id)

    if clinic_id is not None:
        queryset = queryset.filter(clinic_id=clinic_id)

    if weekday is not None:
        queryset = queryset.filter(weekday=weekday)

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset.order_by("weekday", "start_time", "id")


def list_doctor_schedules_for_clinic(
    *,
    clinic_id: int,
    doctor_id: int | None = None,
    weekday: int | None = None,
    is_active: bool | None = None,
) -> QuerySet[DoctorSchedule]:
    queryset = _doctor_schedule_base_queryset().filter(clinic_id=clinic_id)

    if doctor_id is not None:
        queryset = queryset.filter(doctor_id=doctor_id)

    if weekday is not None:
        queryset = queryset.filter(weekday=weekday)

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset.order_by("weekday", "start_time", "id")
