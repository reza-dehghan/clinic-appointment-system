import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_jwt_login_success():
    client = APIClient()

    User.objects.create_user(
        email="jwtuser@test.com", phone="09120000999", password="strongpass123"
    )

    url = reverse("login")

    response = client.post(
        url,
        {
            "email": "jwtuser@test.com",
            "password": "strongpass123",
        },
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_jwt_login_invalid_password():
    client = APIClient()

    User.objects.create_user(
        email="jwtuser2@test.com", phone="09120000888", password="strongpass123"
    )

    url = reverse("login")

    response = client.post(
        url,
        {
            "email": "jwtuser2@test.com",
            "password": "wrongpass",
        },
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_jwt_refresh_flow():
    client = APIClient()

    User.objects.create_user(
        email="jwtuser3@test.com", phone="09120000777", password="strongpass123"
    )

    login_url = reverse("login")
    refresh_url = reverse("refresh")

    login_response = client.post(
        login_url,
        {
            "email": "jwtuser3@test.com",
            "password": "strongpass123",
        },
    )

    refresh_token = login_response.data["refresh"]

    refresh_response = client.post(
        refresh_url,
        {
            "refresh": refresh_token,
        },
    )

    assert refresh_response.status_code == 200
    assert "access" in refresh_response.data
