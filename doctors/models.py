from django.conf import settings
from django.db import models


class Specialty(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"], name="specialty_name_idx"),
            models.Index(fields=["is_active"], name="specialty_active_idx"),
        ]

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="doctor_profile",
    )
    specialties = models.ManyToManyField(
        Specialty,
        related_name="doctors",
        blank=True,
    )
    medical_license_number = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    consultation_fee = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["user"], name="doctor_user_idx"),
            models.Index(
                fields=["medical_license_number"],
                name="doctor_license_idx",
            ),
            models.Index(fields=["is_active"], name="doctor_active_idx"),
        ]

    def __str__(self):
        return str(self.user)


class DoctorClinic(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="clinic_memberships",
    )
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.PROTECT,
        related_name="doctor_memberships",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "clinic"],
                name="unique_doctor_clinic",
            ),
        ]
        indexes = [
            models.Index(
                fields=["doctor", "is_active"],
                name="doc_clinic_doc_act_idx",
            ),
            models.Index(
                fields=["clinic", "is_active"],
                name="doc_clinic_cln_act_idx",
            ),
        ]

    def __str__(self):
        return f"{self.doctor_id} - {self.clinic_id}"


class DoctorSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="schedules",
    )
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.PROTECT,
        related_name="doctor_schedules",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_time__lt=models.F("end_time")),
                name="doctor_schedule_start_before_end",
            ),
            models.CheckConstraint(
                condition=models.Q(slot_duration_minutes__gt=0),
                name="doctor_schedule_duration_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["doctor", "weekday", "is_active"],
                name="doctor_weekday_active_idx",
            ),
            models.Index(
                fields=["clinic", "weekday", "is_active"],
                name="clinic_weekday_active_idx",
            ),
        ]

    def __str__(self):
        return f"{self.doctor_id} - {self.weekday}"
