import factory
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from doctors.models import Doctor, Specialty

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"doctor-user-{n}@test.com")
    phone = factory.Sequence(lambda n: f"091300000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class SpecialtyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Specialty

    name = factory.Sequence(lambda n: f"Specialty {n}")
    slug = factory.Sequence(lambda n: f"specialty-{n}")
    description = "Test specialty"
    is_active = True


class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    medical_license_number = factory.Sequence(lambda n: f"LIC{n:05d}")
    bio = "test bio"
    consultation_fee = 500000
    is_active = True

    @factory.post_generation
    def specialties(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.specialties.add(*extracted)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_list_doctors(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    created_doctors = DoctorFactory.create_batch(3)

    response = api_client.get("/api/doctors/")

    assert response.status_code == 200
    assert len(response.data) >= len(created_doctors)


@pytest.mark.django_db
def test_get_doctor_detail(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()

    response = api_client.get(f"/api/doctors/{doctor.id}/")

    assert response.status_code == 200
    assert response.data["id"] == doctor.id


@pytest.mark.django_db
def test_create_doctor(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    user = UserFactory()
    specialty = SpecialtyFactory()

    payload = {
        "user_id": user.id,
        "medical_license_number": "LIC123",
        "bio": "test bio",
        "consultation_fee": "500000",
        "specialties": [specialty.id],
    }

    before_count = Doctor.objects.count()

    response = api_client.post("/api/doctors/", payload, format="json")

    assert response.status_code == 201
    assert Doctor.objects.count() == before_count + 1


@pytest.mark.django_db
def test_update_doctor(api_client):
    auth_user = UserFactory()
    api_client.force_authenticate(user=auth_user)

    doctor = DoctorFactory()

    response = api_client.patch(
        f"/api/doctors/{doctor.id}/",
        {"bio": "updated bio"},
        format="json",
    )

    doctor.refresh_from_db()

    assert response.status_code == 200
    assert doctor.bio == "updated bio"
