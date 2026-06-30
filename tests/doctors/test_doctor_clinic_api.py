import factory
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"doctor-clinic-user-{n}@test.com")
    phone = factory.Sequence(lambda n: f"091400000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor

    user = factory.SubFactory(UserFactory)
    medical_license_number = factory.Sequence(lambda n: f"DCLIC{n:05d}")
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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_list_doctor_clinics_authenticated(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor_clinic = DoctorClinicFactory()

    response = api_client.get("/api/doctors/doctor-clinics/")

    assert response.status_code == 200
    assert any(item["id"] == doctor_clinic.id for item in response.data)


@pytest.mark.django_db
def test_create_doctor_clinic_authenticated(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()
    clinic = ClinicFactory()

    payload = {
        "doctor_id": doctor.id,
        "clinic_id": clinic.id,
    }

    before_count = DoctorClinic.objects.count()

    response = api_client.post("/api/doctors/doctor-clinics/", payload, format="json")

    assert response.status_code == 201
    assert DoctorClinic.objects.count() == before_count + 1
    assert DoctorClinic.objects.filter(
        doctor_id=doctor.id,
        clinic_id=clinic.id,
    ).exists()


@pytest.mark.django_db
def test_get_doctor_clinic_detail(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor_clinic = DoctorClinicFactory()

    response = api_client.get(f"/api/doctors/doctor-clinics/{doctor_clinic.id}/")

    assert response.status_code == 200
    assert response.data["id"] == doctor_clinic.id


@pytest.mark.django_db
def test_update_doctor_clinic(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor_clinic = DoctorClinicFactory(is_active=True)

    response = api_client.patch(
        f"/api/doctors/doctor-clinics/{doctor_clinic.id}/",
        {"is_active": False},
        format="json",
    )

    doctor_clinic.refresh_from_db()

    assert response.status_code == 200
    assert doctor_clinic.is_active is False
