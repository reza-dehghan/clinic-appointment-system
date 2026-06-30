from django.utils import timezone
from rest_framework import serializers

from appointments.models import Appointment
from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic
from patients.models import Patient


class AvailableSlotSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)


class CreateAppointmentSerializer(serializers.Serializer):
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        source="patient",
        required=False,
    )
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.filter(is_active=True),
        source="doctor",
    )
    clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.filter(is_active=True),
        source="clinic",
    )
    start_time = serializers.DateTimeField()

    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Appointment cannot be booked in the past."
            )

        return value

    def validate(self, attrs):
        doctor = attrs["doctor"]
        clinic = attrs["clinic"]

        if not DoctorClinic.objects.filter(
            doctor=doctor,
            clinic=clinic,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                {"clinic_id": "Selected clinic is not active for this doctor."}
            )

        return attrs


class CancelAppointmentSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)
    clinic = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "doctor",
            "clinic",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class PatientAppointmentListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.user.get_full_name")
    clinic_name = serializers.CharField(source="clinic.name")

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor_name",
            "clinic_name",
            "start_time",
            "end_time",
            "status",
        ]
        read_only_fields = fields


class PatientAppointmentDetailSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.user.get_full_name")
    clinic_name = serializers.CharField(source="clinic.name")

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor_name",
            "clinic_name",
            "start_time",
            "end_time",
            "status",
            "reason",
            "cancellation_reason",
            "created_at",
        ]
        read_only_fields = fields
