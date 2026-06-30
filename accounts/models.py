from django.contrib.auth.base_user import BaseUserManager

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class Role(models.Model):
    class Code(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DOCTOR = "DOCTOR", "Doctor"
        PATIENT = "PATIENT", "Patient"
        CLINIC_STAFF = "CLINIC_STAFF", "Clinic Staff"

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, choices=Code.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.email


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_roles",
    )
    clinic = models.ForeignKey(
        "clinic.Clinic",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="user_roles",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "clinic"],
                condition=models.Q(clinic__isnull=False),
                name="uniq_user_role_clinic",
            ),
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(clinic__isnull=True),
                name="uniq_user_global_role",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "is_active"],
                name="idx_userrole_user_active",
            ),
            models.Index(
                fields=["role", "is_active"],
                name="idx_userrole_role_active",
            ),
            models.Index(
                fields=["clinic", "is_active"],
                name="idx_userrole_clinic_active",
            ),
        ]
