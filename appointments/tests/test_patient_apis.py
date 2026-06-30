import factory
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient

from accounts.tests.factories import PatientFactory
from appointments.models import Appointment
from clinic.models import Clinic
from doctors.models import Doctor

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"patient-api-user-{n}@test.com")
    phone = factory.Sequence(lambda n: f"091800000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor

    user = factory.SubFactory(UserFactory)
    medical_license_number = factory.Sequence(lambda n: f"PALIC{n:05d}")
    bio = "test bio"
    consultation_fee = 500000
    is_active = True


class ClinicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Clinic

    name = factory.Sequence(lambda n: f"Patient API Clinic {n}")
    code = factory.Sequence(lambda n: f"PCLN{n:04d}")
    slug = factory.Sequence(lambda n: f"patient-api-clinic-{n}")
    address_line_1 = "Test address"
    address_line_2 = ""
    city = "Tehran"
    state = "Tehran"
    postal_code = "1234567890"
    country = "Iran"
    phone = "02100000000"
    email = factory.Sequence(lambda n: f"patient-api-clinic-{n}@test.com")
    timezone = "Asia/Tehran"
    is_active = True


def authenticate_patient(client: APIClient, patient) -> None:
    refresh = RefreshToken.for_user(patient.user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")


@pytest.mark.django_db
def test_list_appointments_success():
    client = APIClient()
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 1, 9, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 1, 9, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
        reason="Checkup",
    )
    authenticate_patient(client, patient)

    response = client.get(reverse("patient-appointments-list"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == appointment.id
    assert response.data[0]["doctor_name"] == doctor.user.get_full_name()
    assert response.data[0]["clinic_name"] == clinic.name
    assert response.data[0]["status"] == Appointment.AppointmentStatus.CONFIRMED
    assert "start_time" in response.data[0]
    assert "end_time" in response.data[0]


@pytest.mark.django_db
def test_list_appointments_unauthorized():
    client = APIClient()

    response = client.get(reverse("patient-appointments-list"))

    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }


@pytest.mark.django_db
def test_detail_appointment_success():
    client = APIClient()
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 2, 10, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 2, 10, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
        reason="Consultation",
        cancellation_reason="",
    )
    authenticate_patient(client, patient)

    response = client.get(reverse("appointment-detail", kwargs={"id": appointment.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == appointment.id
    assert response.data["doctor_name"] == doctor.user.get_full_name()
    assert response.data["clinic_name"] == clinic.name
    assert response.data["status"] == Appointment.AppointmentStatus.CONFIRMED
    assert response.data["reason"] == "Consultation"
    assert "created_at" in response.data


@pytest.mark.django_db
def test_detail_appointment_for_other_patient_returns_404():
    client = APIClient()
    patient = PatientFactory()
    other_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=other_patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 2, 11, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 2, 11, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
        reason="Private consultation",
    )
    authenticate_patient(client, patient)

    response = client.get(reverse("appointment-detail", kwargs={"id": appointment.id}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_cancel_appointment_success():
    client = APIClient()
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 3, 11, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 3, 11, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
        reason="Follow-up",
    )
    authenticate_patient(client, patient)

    response = client.post(
        reverse("appointment-cancel", kwargs={"id": appointment.id}),
        {"cancellation_reason": "Unable to attend"},
        format="json",
    )

    appointment.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "cancelled"
    assert appointment.status == Appointment.AppointmentStatus.CANCELLED
    assert appointment.cancellation_reason == "Unable to attend"


@pytest.mark.django_db
def test_cancel_already_cancelled_appointment_fails():
    client = APIClient()
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 4, 12, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 4, 12, 30)),
        status=Appointment.AppointmentStatus.CANCELLED,
        cancellation_reason="Already cancelled",
    )
    authenticate_patient(client, patient)

    response = client.post(
        reverse("appointment-cancel", kwargs={"id": appointment.id}),
        {"cancellation_reason": "Second cancel"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "Appointment cannot be cancelled"


@pytest.mark.django_db
def test_cancel_other_patient_appointment_returns_404():
    client = APIClient()
    patient = PatientFactory()
    other_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    appointment = Appointment.objects.create(
        patient=other_patient,
        doctor=doctor,
        clinic=clinic,
        start_time=timezone.make_aware(timezone.datetime(2026, 7, 5, 12, 0)),
        end_time=timezone.make_aware(timezone.datetime(2026, 7, 5, 12, 30)),
        status=Appointment.AppointmentStatus.CONFIRMED,
    )
    authenticate_patient(client, patient)

    response = client.post(
        reverse("appointment-cancel", kwargs={"id": appointment.id}),
        {"cancellation_reason": "Not mine"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_appointment_uses_authenticated_patient():
    client = APIClient()
    patient = PatientFactory()
    other_patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    from doctors.models import DoctorClinic, DoctorSchedule

    DoctorClinic.objects.create(doctor=doctor, clinic=clinic, is_active=True)
    DoctorSchedule.objects.create(
        doctor=doctor,
        clinic=clinic,
        weekday=2,
        start_time="09:00:00",
        end_time="12:00:00",
        slot_duration_minutes=30,
        is_active=True,
    )
    authenticate_patient(client, patient)

    response = client.post(
        reverse("appointment-create"),
        {
            "patient_id": other_patient.id,
            "doctor_id": doctor.id,
            "clinic_id": clinic.id,
            "start_time": timezone.make_aware(
                timezone.datetime(2026, 7, 1, 9, 0)
            ).isoformat(),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    appointment = Appointment.objects.get(id=response.data["id"])
    assert appointment.patient_id == patient.id


@pytest.mark.django_db
def test_create_appointment_rejects_past_booking():
    client = APIClient()
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    authenticate_patient(client, patient)

    response = client.post(
        reverse("appointment-create"),
        {
            "doctor_id": doctor.id,
            "clinic_id": clinic.id,
            "start_time": (timezone.now() - timezone.timedelta(days=1)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "start_time" in response.data


@pytest.mark.django_db
def test_create_appointment_rejects_invalid_doctor_clinic_combination():
    client = APIClient()
    patient = PatientFactory()
    doctor = DoctorFactory()
    clinic = ClinicFactory()
    authenticate_patient(client, patient)

    response = client.post(
        reverse("appointment-create"),
        {
            "doctor_id": doctor.id,
            "clinic_id": clinic.id,
            "start_time": timezone.make_aware(
                timezone.datetime(2026, 7, 1, 9, 0)
            ).isoformat(),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "clinic_id" in response.data


@pytest.mark.django_db
def test_appointment_endpoints_require_authentication():
    client = APIClient()
    doctor = DoctorFactory()
    clinic = ClinicFactory()

    list_response = client.get(reverse("patient-appointments-list"))
    detail_response = client.get(reverse("appointment-detail", kwargs={"id": 1}))
    cancel_response = client.post(
        reverse("appointment-cancel", kwargs={"id": 1}),
        {"cancellation_reason": "No auth"},
        format="json",
    )
    create_response = client.post(
        reverse("appointment-create"),
        {
            "doctor_id": doctor.id,
            "clinic_id": clinic.id,
            "start_time": timezone.make_aware(
                timezone.datetime(2026, 7, 1, 9, 0)
            ).isoformat(),
        },
        format="json",
    )

    expected_statuses = {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }

    assert list_response.status_code in expected_statuses
    assert detail_response.status_code in expected_statuses
    assert cancel_response.status_code in expected_statuses
    assert create_response.status_code in expected_statuses
