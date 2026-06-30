from django.urls import path

from doctors.views import (
    DoctorClinicDetailView,
    DoctorClinicListCreateView,
    DoctorDetailView,
    DoctorListCreateView,
    DoctorScheduleDetailView,
    DoctorScheduleListCreateView,
)

urlpatterns = [
    path(
        "",
        DoctorListCreateView.as_view(),
        name="doctor-list-create",
    ),
    path(
        "<int:doctor_id>/",
        DoctorDetailView.as_view(),
        name="doctor-detail",
    ),
    path(
        "doctor-clinics/",
        DoctorClinicListCreateView.as_view(),
        name="doctor-clinic-list-create",
    ),
    path(
        "doctor-clinics/<int:doctor_clinic_id>/",
        DoctorClinicDetailView.as_view(),
        name="doctor-clinic-detail",
    ),
    path(
        "doctor-schedules/",
        DoctorScheduleListCreateView.as_view(),
        name="doctor-schedule-list-create",
    ),
    path(
        "doctor-schedules/<int:doctor_schedule_id>/",
        DoctorScheduleDetailView.as_view(),
        name="doctor-schedule-detail",
    ),
]
