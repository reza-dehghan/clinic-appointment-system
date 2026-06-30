from django.urls import path

from clinic.views import ClinicDetailView, ClinicListCreateView

urlpatterns = [
    path("clinics/", ClinicListCreateView.as_view(), name="clinic-list-create"),
    path("clinics/<int:clinic_id>/", ClinicDetailView.as_view(), name="clinic-detail"),
]
