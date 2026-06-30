from rest_framework.permissions import BasePermission


class IsDoctorOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_doctor = getattr(request.user, "doctor_profile", None)
        if user_doctor is None:
            return True

        return obj.doctor.user == request.user
