import factory
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from accounts.tests.factories import PatientFactory
from appointments.models import Appointment
from appointments.selectors import (
    get_available_slots,
    get_patient_active_appointment,
    get_patient_appointment_by_id,
    get_patient_appointments,
)
from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic, DoctorSchedule

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"selector-user-{n}@test.com")
    phone = factory.Sequence(lambda n: f"091900000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor

    user = factory.SubFactory(UserFactory)
    medical_license_number = factory.Sequence(lambda n: f"SELIC{n:05d}")
    bio = "test bio"
    consultation_fee = 500000
    is_active = True


class ClinicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Clinic

    name = factory.Sequence(lambda n: f"Selector Clinic {n}")
    code = factory.Sequence(lambda n: f"SCLN{n:04d}")
    slug = factory.Sequence(lambda n: f"selector-clinic-{n}")
    address_line_1 = "Test address"
    address_line_2 = ""
    city = "Tehran"
    state = "Tehran"
    postal_code = "1234567890"
    country = "Iran"
    phone = "02100000000"
    email = factory.Sequence(lambda n: f"selector-clinic-{n}@test.com")
    timezone = "Asia/Tehran"
    is_active = True


@pytest.mark.django_db
def test_get_available_slots_no_schedule():
    doctor = DoctorFactory()
    clinic = ClinicFactory()

    slots = get_available_slots(doctor, clinic, timezone.datetime(2026, 6, 30).date())

    assert slots == []


@pytest.mark.django_db
def test_get_available_slots_returns_generated_slots():
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinic.objects.create(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )

    slots = get_available_slots(doctor, clinic, timezone.datetime(2026, 6, 30).date())

    assert len(slots) > 0
    assert slots[0]["start_time"] == timezone.datetime(2026, 6, 30, 9, 0)
    assert slots[0]["end_time"] == timezone.datetime(2026, 6, 30, 9, 30)


@pytest.mark.django_db
def test_get_available_slots_excludes_booked_slots():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinic.objects.create(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    booked_start_time = timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 0))
    Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=booked_start_time,
        end_time=timezone.make_aware(timezone.datetime(2026, 6, 30, 9, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )

    slots = get_available_slots(doctor, clinic, timezone.datetime(2026, 6, 30).date())

    assert all(slot["start_time"] != booked_start_time for slot in slots)


@pytest.mark.django_db
def test_get_patient_appointments_filters_by_patient():
    patient = PatientFactory()
    other_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    own_appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 1, 9, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 1, 9, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )
    Appointment.objects.create(
        patient=other_patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 1, 10, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 1, 10, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )

    appointments = list(get_patient_appointments(patient=patient))

    assert appointments == [own_appointment]


@pytest.mark.django_db
def test_get_patient_appointment_by_id_wrong_patient():
    patient = PatientFactory()
    other_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 2, 11, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 2, 11, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )

    with pytest.raises(ObjectDoesNotExist):
        get_patient_appointment_by_id(
            appointment_id=appointment.id,
            patient=other_patient,
        )


@pytest.mark.django_db
def test_get_patient_active_appointment_success():
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 3, 12, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 3, 12, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )

    result = get_patient_active_appointment(
        appointment_id=appointment.id,
        patient=patient,
    )

    assert result == appointment
