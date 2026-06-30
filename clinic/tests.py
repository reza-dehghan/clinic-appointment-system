import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.tests.factories import UserFactory
from clinic.models import Clinic


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def clinic():
    return Clinic.objects.create(
        name="Main Clinic",
        code="MAIN001",
        slug="main-clinic",
        phone="02112345678",
        email="main@clinic.test",
        address_line_1="123 Main St",
        address_line_2="Unit 4",
        city="Tehran",
        state="Tehran",
        postal_code="1234567890",
        country="Iran",
        timezone="Asia/Tehran",
    )


@pytest.fixture
def clinic_list_url():
    return reverse("clinic-list-create")


@pytest.fixture
def clinic_detail_url(clinic):
    return reverse("clinic-detail", kwargs={"clinic_id": clinic.id})


@pytest.mark.django_db
def test_authenticated_user_can_list_clinics(
    authenticated_client, clinic_list_url, clinic
):
    response = authenticated_client.get(clinic_list_url)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == clinic.id
    assert response.data[0]["name"] == clinic.name


@pytest.mark.django_db
def test_authenticated_user_can_create_clinic(authenticated_client, clinic_list_url):
    payload = {
        "name": "North Clinic",
        "code": "NORTH001",
        "slug": "north-clinic",
        "phone": "02187654321",
        "email": "north@clinic.test",
        "address_line_1": "456 North St",
        "address_line_2": "",
        "city": "Mashhad",
        "state": "Razavi Khorasan",
        "postal_code": "9876543210",
        "country": "Iran",
        "timezone": "Asia/Tehran",
    }

    response = authenticated_client.post(clinic_list_url, payload, format="json")

    assert response.status_code == 201
    assert Clinic.objects.filter(code="NORTH001").exists()

    clinic = Clinic.objects.get(code="NORTH001")
    assert response.data["id"] == clinic.id
    assert response.data["name"] == payload["name"]


@pytest.mark.django_db
def test_authenticated_user_can_retrieve_clinic_detail(
    authenticated_client, clinic_detail_url, clinic
):
    response = authenticated_client.get(clinic_detail_url)

    assert response.status_code == 200
    assert response.data["id"] == clinic.id
    assert response.data["code"] == clinic.code


@pytest.mark.django_db
def test_authenticated_user_can_patch_clinic(
    authenticated_client, clinic_detail_url, clinic
):
    payload = {
        "name": "Updated Clinic",
        "phone": "02100000000",
    }

    response = authenticated_client.patch(clinic_detail_url, payload, format="json")

    assert response.status_code == 200

    clinic.refresh_from_db()
    assert clinic.name == "Updated Clinic"
    assert clinic.phone == "02100000000"
    assert response.data["name"] == "Updated Clinic"


@pytest.mark.django_db
def test_unauthenticated_list_returns_401(api_client, clinic_list_url, clinic):
    response = api_client.get(clinic_list_url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_unauthenticated_create_returns_401(api_client, clinic_list_url):
    payload = {
        "name": "North Clinic",
        "code": "NORTH002",
        "slug": "north-clinic-2",
        "phone": "02187654321",
        "email": "north2@clinic.test",
        "address_line_1": "456 North St",
        "address_line_2": "",
        "city": "Mashhad",
        "state": "Razavi Khorasan",
        "postal_code": "9876543210",
        "country": "Iran",
        "timezone": "Asia/Tehran",
    }

    response = api_client.post(clinic_list_url, payload, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_unauthenticated_detail_returns_401(api_client, clinic_detail_url, clinic):
    response = api_client.get(clinic_detail_url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_unauthenticated_patch_returns_401(api_client, clinic_detail_url, clinic):
    response = api_client.patch(clinic_detail_url, {"name": "Blocked"}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_detail_missing_clinic_returns_404(authenticated_client):
    url = reverse("clinic-detail", kwargs={"clinic_id": 999999})

    response = authenticated_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_authenticated_patch_missing_clinic_returns_404(authenticated_client):
    url = reverse("clinic-detail", kwargs={"clinic_id": 999999})

    response = authenticated_client.patch(url, {"name": "Missing"}, format="json")

    assert response.status_code == 404
