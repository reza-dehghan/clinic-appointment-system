from datetime import date as date_type

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.selectors import (
    get_available_slots,
    get_patient_active_appointment,
    get_patient_appointment_by_id,
    get_patient_appointments,
)
from appointments.serializers import (
    AppointmentSerializer,
    AvailableSlotSerializer,
    CancelAppointmentSerializer,
    CreateAppointmentSerializer,
    PatientAppointmentDetailSerializer,
    PatientAppointmentListSerializer,
)
from appointments.services import book_appointment, cancel_appointment
from clinic.models import Clinic
from doctors.models import Doctor
from patients.models import Patient


class DoctorAvailableSlotsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت اسلات‌های خالی پزشک",
        description="این API اسلات‌های قابل رزرو یک پزشک را در یک کلینیک مشخص و برای یک تاریخ معین برمی‌گرداند.",
        tags=["Appointments"],
        parameters=[
            OpenApiParameter(
                name="clinic_id",
                type=int,
                required=True,
                description="شناسه کلینیکی که نوبت در آن بررسی می‌شود.",
            ),
            OpenApiParameter(
                name="date",
                type=str,
                required=True,
                description="تاریخ موردنظر با فرمت YYYY-MM-DD.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=AvailableSlotSerializer(many=True),
                description="لیست اسلات‌های خالی با موفقیت دریافت شد.",
            ),
            400: OpenApiResponse(description="پارامترهای ورودی نامعتبر یا ناقص هستند."),
            404: OpenApiResponse(description="پزشک یا کلینیک موردنظر پیدا نشد."),
        },
    )
    def get(self, request, doctor_id: int) -> Response:
        clinic_id = request.query_params.get("clinic_id")
        date_value = request.query_params.get("date")

        if not clinic_id or not date_value:
            return Response(
                {"detail": "clinic_id and date query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            clinic_id = int(clinic_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "clinic_id must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_date = date_type.fromisoformat(date_value)
        except ValueError:
            return Response(
                {"detail": "date must be in YYYY-MM-DD format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor = get_object_or_404(Doctor, id=doctor_id)
        clinic = get_object_or_404(Clinic, id=clinic_id)

        available_slots = get_available_slots(
            doctor=doctor,
            clinic=clinic,
            date=target_date,
        )
        serializer = AvailableSlotSerializer(available_slots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AppointmentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="رزرو نوبت",
        description="این API برای بیمار احراز هویت‌شده یک نوبت جدید نزد پزشک و کلینیک انتخاب‌شده ثبت می‌کند.",
        tags=["Appointments"],
        request=CreateAppointmentSerializer,
        responses={
            201: OpenApiResponse(
                response=AppointmentSerializer,
                description="نوبت با موفقیت رزرو شد.",
            ),
            400: OpenApiResponse(description="اطلاعات ورودی نامعتبر است یا رزرو امکان‌پذیر نیست."),
        },
    )
    def post(self, request) -> Response:
        serializer = CreateAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        patient = request.user.patient_profile
        validated_data = serializer.validated_data
        doctor = validated_data["doctor"]
        clinic = validated_data["clinic"]
        start_time = validated_data["start_time"]

        patient = get_object_or_404(Patient, id=patient.id)
        doctor = get_object_or_404(Doctor, id=doctor.id)
        clinic = get_object_or_404(Clinic, id=clinic.id)

        try:
            appointment = book_appointment(
                patient=patient,
                doctor=doctor,
                clinic=clinic,
                start_time=start_time,
            )
        except DjangoValidationError as exc:
            messages = exc.messages or ["Unable to book appointment."]
            return Response(
                {"detail": messages[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output_serializer = AppointmentSerializer(appointment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PatientAppointmentListAPIView(ListAPIView):
    serializer_class = PatientAppointmentListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت لیست نوبت‌های بیمار",
        description="این API فهرست نوبت‌های مربوط به بیمار جاری را نمایش می‌دهد.",
        tags=["Appointments"],
        responses={
            200: OpenApiResponse(
                response=PatientAppointmentListSerializer(many=True),
                description="لیست نوبت‌های بیمار با موفقیت دریافت شد.",
            ),
        },
    )

    def get_queryset(self):
        patient = self.request.user.patient_profile
        return get_patient_appointments(patient=patient)


class PatientAppointmentDetailAPIView(RetrieveAPIView):
    serializer_class = PatientAppointmentDetailSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت جزئیات نوبت بیمار",
        description="این API جزئیات کامل یک نوبت متعلق به بیمار جاری را بر اساس شناسه برمی‌گرداند.",
        tags=["Appointments"],
        responses={
            200: OpenApiResponse(
                response=PatientAppointmentDetailSerializer,
                description="جزئیات نوبت با موفقیت دریافت شد.",
            ),
            404: OpenApiResponse(description="نوبت موردنظر پیدا نشد."),
        },
    )

    def get_object(self):
        patient = self.request.user.patient_profile
        appointment_id = self.kwargs["id"]

        try:
            return get_patient_appointment_by_id(
                appointment_id=appointment_id,
                patient=patient,
            )
        except ObjectDoesNotExist as exc:
            raise Http404 from exc


class CancelAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="لغو نوبت",
        description="این API نوبت فعال بیمار را لغو می‌کند و در صورت نیاز دلیل لغو را ثبت می‌کند.",
        tags=["Appointments"],
        request=CancelAppointmentSerializer,
        responses={
            200: OpenApiResponse(
                description="نوبت با موفقیت لغو شد.",
            ),
            400: OpenApiResponse(description="لغو نوبت امکان‌پذیر نیست یا داده‌های ورودی نامعتبر است."),
            404: OpenApiResponse(description="نوبت فعال موردنظر پیدا نشد."),
        },
    )
    def post(self, request, id):
        patient = request.user.patient_profile

        try:
            appointment = get_patient_active_appointment(
                appointment_id=id,
                patient=patient,
            )
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cancel_appointment(
                appointment=appointment,
                cancellation_reason=serializer.validated_data.get(
                    "cancellation_reason"
                ),
            )
        except DjangoValidationError as exc:
            messages = exc.messages or ["Appointment cannot be cancelled"]
            return Response(
                {"detail": messages[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"status": "cancelled"})
