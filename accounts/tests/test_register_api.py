import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Role, User, UserRole
from patients.models import Patient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def register_url():
    return reverse("register")


@pytest.mark.django_db
def test_register_patient_success(api_client, register_url):
    role = Role.objects.create(name="Patient", code=Role.Code.PATIENT)

    data = {
        "phone_number": "09120000001",
        "password": "strongpass123",
        "first_name": "Ali",
        "last_name": "Ahmadi",
        "national_code": "1234567890",
    }

    response = api_client.post(register_url, data, format="json")

    assert response.status_code == 201

    user = User.objects.get(phone="09120000001")

    assert Patient.objects.filter(user=user, national_code="1234567890").exists()
    assert UserRole.objects.filter(user=user, role=role).exists()


@pytest.mark.django_db
def test_register_duplicate_phone(api_client, register_url):
    Role.objects.create(name="Patient", code=Role.Code.PATIENT)

    data = {
        "phone_number": "09120000002",
        "password": "strongpass123",
        "first_name": "Ali",
        "last_name": "Ahmadi",
        "national_code": "1234567891",
    }

    first_response = api_client.post(register_url, data, format="json")
    response = api_client.post(register_url, data, format="json")

    assert first_response.status_code == 201
    assert response.status_code == 400
    assert response.data["phone_number"] == ["Phone number already registered."]
