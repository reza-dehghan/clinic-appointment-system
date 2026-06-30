from django.urls import path

from .views import (
    AppointmentCreateAPIView,
    CancelAppointmentAPIView,
    DoctorAvailableSlotsAPIView,
    PatientAppointmentDetailAPIView,
    PatientAppointmentListAPIView,
)

urlpatterns = [
    path(
        "doctors/<int:doctor_id>/available-slots/",
        DoctorAvailableSlotsAPIView.as_view(),
        name="doctor-available-slots",
    ),
    path(
        "appointments/",
        AppointmentCreateAPIView.as_view(),
        name="appointment-create",
    ),
    path(
        "appointments/<int:id>/",
        PatientAppointmentDetailAPIView.as_view(),
        name="appointment-detail",
    ),
    path(
        "appointments/<int:id>/cancel/",
        CancelAppointmentAPIView.as_view(),
        name="appointment-cancel",
    ),
    path(
        "patients/me/appointments/",
        PatientAppointmentListAPIView.as_view(),
        name="patient-appointments-list",
    ),
]
