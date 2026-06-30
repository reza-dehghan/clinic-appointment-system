from typing import TypedDict, Unpack

from django.db import transaction

from clinic.models import Clinic


class ClinicUpdateData(TypedDict, total=False):
    name: str
    code: str
    slug: str
    phone: str | None
    email: str | None
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str | None
    timezone: str | None
    is_active: bool


@transaction.atomic
def create_clinic(
    *,
    name: str,
    code: str,
    slug: str,
    phone: str | None = None,
    email: str | None = None,
    address_line_1: str | None = None,
    address_line_2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    timezone: str | None = None,
) -> Clinic:
    return Clinic.objects.create(
        name=name,
        code=code,
        slug=slug,
        phone=phone or "",
        email=email or "",
        address_line_1=address_line_1 or "",
        address_line_2=address_line_2 or "",
        city=city or "",
        state=state or "",
        postal_code=postal_code or "",
        country=country or "",
        timezone=timezone or "",
    )


@transaction.atomic
def update_clinic(
    clinic: Clinic,
    **data: Unpack[ClinicUpdateData],
) -> Clinic:
    for field, value in data.items():
        setattr(clinic, field, value)

    clinic.save()
    return clinic


@transaction.atomic
def deactivate_clinic(
    clinic: Clinic,
) -> Clinic:
    clinic.is_active = False
    clinic.save()
    return clinic
