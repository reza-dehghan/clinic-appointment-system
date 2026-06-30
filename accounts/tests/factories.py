import factory
from django.contrib.auth import get_user_model

from accounts.models import Role, UserRole
from patients.models import Patient

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    phone = factory.Sequence(lambda n: f"091200000{n:02d}")
    first_name = "Test"
    last_name = "User"
    is_active = True


class PatientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Patient

    user = factory.SubFactory(UserFactory)
    national_code = factory.Sequence(lambda n: f"12345678{n:02d}")


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"ROLE_{n}")
    code = factory.Iterator([choice for choice, _ in Role.Code.choices])


class UserRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserRole

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    clinic = None
    is_active = True
