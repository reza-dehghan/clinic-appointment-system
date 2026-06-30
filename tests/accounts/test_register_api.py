import pytest
from rest_framework.test import APIClient

from accounts.models import User, Role, UserRole
from patients.models import Patient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def register_url():
    return "/api/auth/register/"


@pytest.mark.django_db
def test_register_patient_success(api_client, register_url):

    Role.objects.get_or_create(
        code=Role.Code.PATIENT,
        defaults={"name": "Patient"},
    )

    payload = {
        "phone_number": "09120000000",
        "password": "strong-pass-123",
        "first_name": "Ali",
        "last_name": "Ahmadi",
        "national_code": "1234567890",
    }

    response = api_client.post(register_url, payload, format="json")

    assert response.status_code == 201

    user = User.objects.get(phone="09120000000")
    patient = Patient.objects.get(user=user)

    assert patient.national_code == "1234567890"

    role = UserRole.objects.get(user=user)
    assert role.role.code == Role.Code.PATIENT
