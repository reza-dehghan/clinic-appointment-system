import factory
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from accounts.tests.factories import PatientFactory
from appointments.models import Appointment
from appointments.services import (
    book_appointment,
    cancel_appointment,
    generate_schedule_slots,
)
from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic, DoctorSchedule

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"booking-user-{n}@test.com")
    phone = factory.Sequence(lambda n: f"091700000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor

    user = factory.SubFactory(UserFactory)
    medical_license_number = factory.Sequence(lambda n: f"BKLIC{n:05d}")
    bio = "test bio"
    consultation_fee = 500000
    is_active = True


class ClinicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Clinic

    name = factory.Sequence(lambda n: f"Booking Clinic {n}")
    code = factory.Sequence(lambda n: f"BCLN{n:04d}")
    slug = factory.Sequence(lambda n: f"booking-clinic-{n}")
    address_line_1 = "Test address"
    address_line_2 = ""
    city = "Tehran"
    state = "Tehran"
    postal_code = "1234567890"
    country = "Iran"
    phone = "02100000000"
    email = factory.Sequence(lambda n: f"booking-clinic-{n}@test.com")
    timezone = "Asia/Tehran"
    is_active = True


class DoctorClinicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorClinic

    doctor = factory.SubFactory(DoctorFactory)
    clinic = factory.SubFactory(ClinicFactory)
    is_active = True


def test_generate_schedule_slots_normal_case():
    doctor_schedule = DoctorSchedule(
        start_time=timezone.datetime(2026, 6, 30, 9, 0).time(),
        end_time=timezone.datetime(2026, 6, 30, 12, 0).time(),
        slot_duration_minutes=30,
    )

    slots = generate_schedule_slots(doctor_schedule, timezone.datetime(2026, 6, 30).date())

    assert len(slots) == 6
    assert slots == [
        timezone.datetime(2026, 6, 30, 9, 0),
        timezone.datetime(2026, 6, 30, 9, 30),
        timezone.datetime(2026, 6, 30, 10, 0),
        timezone.datetime(2026, 6, 30, 10, 30),
        timezone.datetime(2026, 6, 30, 11, 0),
        timezone.datetime(2026, 6, 30, 11, 30),
    ]


def test_generate_schedule_slots_exact_boundary():
    doctor_schedule = DoctorSchedule(
        start_time=timezone.datetime(2026, 6, 30, 9, 0).time(),
        end_time=timezone.datetime(2026, 6, 30, 10, 0).time(),
        slot_duration_minutes=60,
    )

    slots = generate_schedule_slots(doctor_schedule, timezone.datetime(2026, 6, 30).date())

    assert slots == [timezone.datetime(2026, 6, 30, 9, 0)]


def test_generate_schedule_slots_duration_exceeds_window():
    doctor_schedule = DoctorSchedule(
        start_time=timezone.datetime(2026, 6, 30, 9, 0).time(),
        end_time=timezone.datetime(2026, 6, 30, 9, 30).time(),
        slot_duration_minutes=60,
    )

    slots = generate_schedule_slots(doctor_schedule, timezone.datetime(2026, 6, 30).date())

    assert slots == []


@pytest.mark.django_db
def test_book_appointment_no_schedule():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0))

    with pytest.raises(ValidationError, match="No active schedule found"):
        book_appointment(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            start_time=start_time,
        )


@pytest.mark.django_db
def test_book_appointment_inactive_membership():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=False)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0))

    with pytest.raises(ValidationError, match="active clinic membership"):
        book_appointment(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            start_time=start_time,
        )


@pytest.mark.django_db
def test_book_appointment_slot_misaligned():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 10))

    with pytest.raises(ValidationError, match="does not align with the schedule slot duration"):
        book_appointment(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            start_time=start_time,
        )


@pytest.mark.django_db
def test_book_appointment_successfully():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0))

    appointment = book_appointment(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=start_time,
    )

    assert Appointment.objects.filter(id=appointment.id).exists()
    assert appointment.start_time == start_time
    assert appointment.end_time == timezone.make_aware(
        timezone.datetime(2026, 6, 30, 9, 30)
    )


@pytest.mark.django_db
def test_book_appointment_rejects_double_booking():
    patient = PatientFactory()
    another_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0))

    book_appointment(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=start_time,
    )

    with pytest.raises(ValidationError):
        book_appointment(
            patient=another_patient,
            doctor=doctor,
            clinic=clinic,
            start_time=start_time,
        )


@pytest.mark.django_db
def test_book_appointment_converts_integrity_error_to_validation_error(monkeypatch):
    patient = PatientFactory()
    another_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0))

    book_appointment(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=start_time,
    )

    def raise_integrity_error(**kwargs):
        raise IntegrityError("duplicate key value violates unique constraint")

    monkeypatch.setattr(Appointment.objects, "create", raise_integrity_error)

    with pytest.raises(ValidationError, match="This appointment slot is already booked."):
        book_appointment(
            patient=another_patient,
            doctor=doctor,
            clinic=clinic,
            start_time=start_time,
        )


@pytest.mark.django_db
def test_book_appointment_rejects_slot_outside_schedule():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    invalid_start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 15, 0))

    with pytest.raises(ValidationError):
        book_appointment(
            patient=patient,
            doctor=doctor,
            clinic=clinic,
            start_time=invalid_start_time,
        )


@pytest.mark.django_db
def test_cancel_appointment_success():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )

    cancelled_appointment = cancel_appointment(
        appointment=appointment,
        cancellation_reason="Patient requested cancellation",
    )

    assert cancelled_appointment.status == Appointment.AppointmentStatus.CANCELLED
    assert (
        cancelled_appointment.cancellation_reason
        == "Patient requested cancellation"
    )


@pytest.mark.django_db
def test_cancel_appointment_invalid_status():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 6, 30, 10, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 6, 30, 10, 30)),
        status=Appointment.AppointmentStatus.COMPLETED,
    )

    with pytest.raises(ValidationError, match="Appointment cannot be cancelled"):
        cancel_appointment(appointment=appointment)
