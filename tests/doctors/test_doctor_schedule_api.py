import factory
import pytest
from django.contrib.auth import get_user_model

from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic, DoctorSchedule
from rest_framework.test import APIClient

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"doctor-schedule-user-{n}@test.com")
    phone = factory.Sequence(lambda n: f"091500000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor

    user = factory.SubFactory(UserFactory)
    medical_license_number = factory.Sequence(lambda n: f"DSLIC{n:05d}")
    bio = "test bio"
    consultation_fee = 500000
    is_active = True


class ClinicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Clinic

    name = factory.Sequence(lambda n: f"Clinic {n}")
    code = factory.Sequence(lambda n: f"CLN{n:04d}")
    slug = factory.Sequence(lambda n: f"clinic-{n}")
    address_line_1 = "Test address"
    address_line_2 = ""
    city = "Tehran"
    state = "Tehran"
    postal_code = "1234567890"
    country = "Iran"
    phone = "02100000000"
    email = factory.Sequence(lambda n: f"clinic-{n}@test.com")
    timezone = "Asia/Tehran"
    is_active = True


class DoctorClinicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorClinic

    doctor = factory.SubFactory(DoctorFactory)
    clinic = factory.SubFactory(ClinicFactory)
    is_active = True


class DoctorScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorSchedule

    doctor = factory.SubFactory(DoctorFactory)
    clinic = factory.SubFactory(ClinicFactory)
    weekday = 1
    start_time = "09:00:00"
    end_time = "12:00:00"
    slot_duration_minutes = 30
    is_active = True


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_doctor_schedule_successfully(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)

    payload = {
        "doctor_id": doctor.id,
        "clinic_id": clinic.id,
        "weekday": 1,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_duration_minutes": 30,
    }

    before_count = DoctorSchedule.objects.count()

    response = api_client.post("/api/doctors/doctor-schedules/", payload, format="json")

    assert response.status_code == 201
    assert DoctorSchedule.objects.count() == before_count + 1
    assert DoctorSchedule.objects.filter(
        doctor_id=doctor.id,
        clinic_id=clinic.id,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
    ).exists()


@pytest.mark.django_db
def test_reject_overlapping_doctor_schedules(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

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

    payload = {
        "doctor_id": doctor.id,
        "clinic_id": clinic.id,
        "weekday": 1,
        "start_time": "11:00:00",
        "end_time": "13:00:00",
        "slot_duration_minutes": 30,
    }

    response = api_client.post("/api/doctors/doctor-schedules/", payload, format="json")

    assert response.status_code == 400
    assert (
        DoctorSchedule.objects.filter(
            doctor_id=doctor.id,
            clinic_id=clinic.id,
            weekday=1,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_reject_schedule_without_active_doctor_clinic_membership(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()
    clinic = ClinicFactory()

    payload = {
        "doctor_id": doctor.id,
        "clinic_id": clinic.id,
        "weekday": 2,
        "start_time": "14:00:00",
        "end_time": "17:00:00",
        "slot_duration_minutes": 20,
    }

    response = api_client.post("/api/doctors/doctor-schedules/", payload, format="json")

    assert response.status_code == 400
    assert DoctorSchedule.objects.count() == 0


@pytest.mark.django_db
def test_update_doctor_schedule_successfully(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    doctor_schedule = DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=3,
        start_time="08:00:00",
        end_time="10:00:00",
        slot_duration_minutes=20,
        is_active=True,
    )

    response = api_client.patch(
        f"/api/doctors/doctor-schedules/{doctor_schedule.id}/",
        {
            "end_time": "11:00:00",
            "slot_duration_minutes": 30,
        },
        format="json",
    )

    doctor_schedule.refresh_from_db()

    assert response.status_code == 200
    assert str(doctor_schedule.end_time) == "11:00:00"
    assert doctor_schedule.slot_duration_minutes == 30


@pytest.mark.django_db
def test_deactivate_doctor_schedule_soft_delete(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    doctor_schedule = DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=4,
        start_time="10:00:00",
        end_time="13:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )

    response = api_client.delete(f"/api/doctors/doctor-schedules/{doctor_schedule.id}/")

    doctor_schedule.refresh_from_db()

    assert response.status_code == 200
    assert doctor_schedule.is_active is False


@pytest.mark.django_db
def test_doctor_cannot_modify_another_doctor_schedule(api_client):
    owner_doctor = DoctorFactory()
    other_doctor = DoctorFactory()
    api_client.force_authenticate(user=owner_doctor.user)

    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=owner_doctor, clinic=clinic, is_active=True)
    DoctorClinicFactory(doctor=other_doctor, clinic=clinic, is_active=True)
    doctor_schedule = DoctorSchedule.objects.create(
        doctor=other_doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )

    response = api_client.patch(
        f"/api/doctors/doctor-schedules/{doctor_schedule.id}/",
        {"end_time": "11:00:00"},
        format="json",
    )

    doctor_schedule.refresh_from_db()

    assert response.status_code == 403
    assert str(doctor_schedule.end_time) == "12:00:00"


@pytest.mark.django_db
def test_doctor_schedule_endpoints_require_authentication(api_client):
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    DoctorClinicFactory(doctor=doctor, clinic=clinic, is_active=True)
    doctor_schedule = DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=1,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )

    list_response = api_client.get("/api/doctors/doctor-schedules/")
    create_response = api_client.post(
        "/api/doctors/doctor-schedules/",
        {
            "doctor_id": doctor.id,
            "clinic_id": clinic.id,
            "weekday": 1,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "slot_duration_minutes": 30,
        },
        format="json",
    )
    detail_response = api_client.get(
        f"/api/doctors/doctor-schedules/{doctor_schedule.id}/"
    )
    patch_response = api_client.patch(
        f"/api/doctors/doctor-schedules/{doctor_schedule.id}/",
        {"end_time": "11:00:00"},
        format="json",
    )
    delete_response = api_client.delete(
        f"/api/doctors/doctor-schedules/{doctor_schedule.id}/"
    )

    expected_statuses = {401, 403}

    assert list_response.status_code in expected_statuses
    assert create_response.status_code in expected_statuses
    assert detail_response.status_code in expected_statuses
    assert patch_response.status_code in expected_statuses
    assert delete_response.status_code in expected_statuses
