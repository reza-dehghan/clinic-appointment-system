from rest_framework import serializers

from clinic.models import Clinic


class ClinicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            "name",
            "code",
            "slug",
            "phone",
            "email",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "timezone",
        ]
        extra_kwargs = {
            "phone": {"required": False, "allow_blank": True},
            "email": {"required": False, "allow_blank": True},
            "address_line_2": {"required": False, "allow_blank": True},
        }


class ClinicUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            "name",
            "code",
            "slug",
            "phone",
            "email",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "timezone",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "code": {"required": False},
            "slug": {"required": False},
            "phone": {"required": False, "allow_blank": True},
            "email": {"required": False, "allow_blank": True},
            "address_line_1": {"required": False},
            "address_line_2": {"required": False, "allow_blank": True},
            "city": {"required": False},
            "state": {"required": False},
            "postal_code": {"required": False},
            "country": {"required": False},
            "timezone": {"required": False},
        }


class ClinicReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            "id",
            "name",
            "code",
            "slug",
            "phone",
            "email",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]
