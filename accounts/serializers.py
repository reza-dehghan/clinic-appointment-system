from rest_framework import serializers

from accounts.models import User
from patients.models import Patient


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=64)
    last_name = serializers.CharField(max_length=64)
    national_code = serializers.CharField(max_length=10)

    def validate_phone_number(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already registered.")
        return value

    def validate_national_code(self, value):
        if Patient.objects.filter(national_code=value).exists():
            raise serializers.ValidationError("National code already registered.")
        return value
