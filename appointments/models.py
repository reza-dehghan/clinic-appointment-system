from django.db import models


class TimeSlot(models.Model):
    class TimeSlotStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        BLOCKED = "blocked", "Blocked"

    doctor = models.ForeignKey(
        "doctors.Doctor",
        on_delete=models.PROTECT,
        related_name="time_slots",
    )
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.PROTECT,
        related_name="time_slots",
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=TimeSlotStatus.choices,
        default=TimeSlotStatus.AVAILABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "start_at"],
                name="unique_doctor_timeslot_start",
            ),
            models.CheckConstraint(
                condition=models.Q(start_at__lt=models.F("end_at")),
                name="timeslot_start_before_end",
            ),
        ]
        indexes = [
            models.Index(
                fields=["doctor", "start_at"], name="timeslot_doctor_start_idx"
            ),
            models.Index(
                fields=["clinic", "start_at"], name="timeslot_clinic_start_idx"
            ),
            models.Index(
                fields=["status", "start_at"], name="timeslot_status_start_idx"
            ),
        ]

    def __str__(self):
        return f"{self.doctor_id} - {self.start_at}"


class Appointment(models.Model):
    class AppointmentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        NO_SHOW = "no_show", "No Show"

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
    )
    reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "start_time"],
                name="unique_doctor_appointment_start",
            ),
            models.CheckConstraint(
                condition=models.Q(start_time__lt=models.F("end_time")),
                name="appointment_start_before_end",
            ),
        ]
        indexes = [
            models.Index(
                fields=["patient", "status"], name="appointment_patient_status_idx"
            ),
            models.Index(
                fields=["doctor", "status"], name="appointment_doctor_status_idx"
            ),
            models.Index(
                fields=["clinic", "status"], name="appointment_clinic_status_idx"
            ),
            models.Index(
                fields=["doctor", "start_time"], name="appointment_doctor_start_idx"
            ),
            models.Index(
                fields=["clinic", "start_time"], name="appointment_clinic_start_idx"
            ),
            models.Index(
                fields=["status", "start_time"], name="appointment_status_start_idx"
            ),
        ]

    def __str__(self):
        return f"{self.patient_id} - {self.start_time}"
