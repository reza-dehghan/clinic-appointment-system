from django.db.models import QuerySet

from .models import Clinic


def get_clinic_by_id(clinic_id: int) -> Clinic:
    return Clinic.objects.get(id=clinic_id)


def get_active_clinics() -> QuerySet[Clinic]:
    return Clinic.objects.filter(is_active=True)


def list_clinics() -> QuerySet[Clinic]:
    return Clinic.objects.all()
