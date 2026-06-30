from rest_framework import serializers

from accounts.models import User
from clinic.models import Clinic
from doctors.models import Doctor, DoctorClinic, DoctorSchedule, Specialty


class DoctorCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
    )
    specialties = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Doctor
        fields = (
            "user_id",
            "medical_license_number",
            "bio",
            "consultation_fee",
            "specialties",
        )


class DoctorUpdateSerializer(serializers.ModelSerializer):
    specialties = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Doctor
        fields = (
            "bio",
            "consultation_fee",
            "specialties",
            "is_active",
        )
        extra_kwargs = {
            "bio": {"required": False},
            "consultation_fee": {"required": False},
            "specialties": {"required": False},
            "is_active": {"required": False},
        }


class DoctorReadSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = (
            "id",
            "user",
            "medical_license_number",
            "bio",
            "consultation_fee",
            "specialties",
            "is_active",
            "created_at",
        )

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "phone_number": obj.user.phone,
            "email": obj.user.email,
        }


class DoctorClinicCreateSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        source="doctor",
    )
    clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.all(),
        source="clinic",
    )
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = DoctorClinic
        fields = [
            "doctor_id",
            "clinic_id",
            "is_active",
        ]


class DoctorClinicUpdateSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = DoctorClinic
        fields = [
            "is_active",
        ]


class DoctorClinicReadSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source="doctor.id")
    clinic_id = serializers.IntegerField(source="clinic.id")

    class Meta:
        model = DoctorClinic
        fields = [
            "id",
            "doctor_id",
            "clinic_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DoctorScheduleCreateSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        source="doctor",
    )
    clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.all(),
        source="clinic",
    )
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = DoctorSchedule
        fields = [
            "doctor_id",
            "clinic_id",
            "weekday",
            "start_time",
            "end_time",
            "slot_duration_minutes",
            "is_active",
        ]


class DoctorScheduleUpdateSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = DoctorSchedule
        fields = [
            "weekday",
            "start_time",
            "end_time",
            "slot_duration_minutes",
            "is_active",
        ]
        extra_kwargs = {
            "weekday": {"required": False},
            "start_time": {"required": False},
            "end_time": {"required": False},
            "slot_duration_minutes": {"required": False},
            "is_active": {"required": False},
        }


class DoctorScheduleReadSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source="doctor.id")
    clinic_id = serializers.IntegerField(source="clinic.id")

    class Meta:
        model = DoctorSchedule
        fields = [
            "id",
            "doctor_id",
            "clinic_id",
            "weekday",
            "start_time",
            "end_time",
            "slot_duration_minutes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
