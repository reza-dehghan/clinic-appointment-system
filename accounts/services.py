from django.db import transaction

from accounts.models import Role, User, UserRole
from patients.models import Patient


def register_patient(*, phone_number, password, first_name, last_name, national_code):
    with transaction.atomic():
        user = User.objects.create_user(
            email=f"{phone_number}@local.mediva",
            phone=phone_number,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        Patient.objects.create(
            user=user,
            national_code=national_code,
        )

        role = Role.objects.get(code=Role.Code.PATIENT)

        UserRole.objects.create(
            user=user,
            role=role,
            clinic=None,
            is_active=True,
        )

        return user
