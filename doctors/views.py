from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.permissions import IsDoctorOwner
from doctors.selectors import (
    get_doctor_by_id,
    get_doctor_clinic,
    get_doctor_schedule,
    list_doctor_clinics,
    list_doctor_schedules,
    list_doctors,
)
from doctors.serializers import (
    DoctorClinicCreateSerializer,
    DoctorClinicReadSerializer,
    DoctorClinicUpdateSerializer,
    DoctorCreateSerializer,
    DoctorReadSerializer,
    DoctorScheduleCreateSerializer,
    DoctorScheduleReadSerializer,
    DoctorScheduleUpdateSerializer,
    DoctorUpdateSerializer,
)
from doctors.services import (
    create_doctor,
    create_doctor_clinic,
    create_doctor_schedule,
    deactivate_doctor_schedule,
    update_doctor,
    update_doctor_clinic,
    update_doctor_schedule,
)
from doctors.models import Doctor


class DoctorListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت لیست پزشکان",
        description="این API فهرست پزشکان ثبت‌شده را برای استفاده در جست‌وجو، انتخاب پزشک و نمایش اطلاعات پایه برمی‌گرداند.",
        tags=["Doctors"],
        responses={
            200: OpenApiResponse(
                response=DoctorReadSerializer(many=True),
                description="لیست پزشکان با موفقیت دریافت شد.",
            ),
        },
    )
    def get(self, request) -> Response:
        doctors = list_doctors()
        serializer = DoctorReadSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="ایجاد پروفایل پزشک",
        description="این API یک پروفایل پزشک جدید را با کاربر مرتبط، شماره نظام پزشکی، بیوگرافی و تخصص‌ها ایجاد می‌کند.",
        tags=["Doctors"],
        request=DoctorCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=DoctorReadSerializer,
                description="پروفایل پزشک با موفقیت ایجاد شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است."),
        },
    )
    def post(self, request) -> Response:
        serializer = DoctorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data.copy()
        validated_data["user_id"] = validated_data.pop("user").id
        validated_data["specialties"] = [
            specialty.id for specialty in validated_data.get("specialties", [])
        ]

        doctor = create_doctor(validated_data)
        response_serializer = DoctorReadSerializer(doctor)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DoctorDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت جزئیات پزشک",
        description="این API اطلاعات کامل یک پزشک را بر اساس شناسه برمی‌گرداند.",
        tags=["Doctors"],
        responses={
            200: OpenApiResponse(
                response=DoctorReadSerializer,
                description="اطلاعات پزشک با موفقیت دریافت شد.",
            ),
            404: OpenApiResponse(description="پزشک موردنظر پیدا نشد."),
        },
    )
    def get(self, request, doctor_id: int) -> Response:
        try:
            doctor = get_doctor_by_id(doctor_id)
        except DoctorReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorReadSerializer(doctor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="به‌روزرسانی پزشک",
        description="این API برای ویرایش بخشی از اطلاعات پزشک مانند بیوگرافی، هزینه ویزیت، تخصص‌ها و وضعیت فعال بودن استفاده می‌شود.",
        tags=["Doctors"],
        request=DoctorUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=DoctorReadSerializer,
                description="اطلاعات پزشک با موفقیت به‌روزرسانی شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است."),
            404: OpenApiResponse(description="پزشک موردنظر پیدا نشد."),
        },
    )
    def patch(self, request, doctor_id: int) -> Response:
        try:
            doctor = get_doctor_by_id(doctor_id)
        except DoctorReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data.copy()
        if "specialties" in validated_data:
            validated_data["specialties"] = [
                specialty.id for specialty in validated_data["specialties"]
            ]

        doctor = update_doctor(doctor, validated_data)
        response_serializer = DoctorReadSerializer(doctor)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class DoctorClinicListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت لیست ارتباط پزشک و کلینیک",
        description="این API لیست عضویت پزشکان در کلینیک‌ها را برمی‌گرداند و می‌تواند بر اساس پزشک، کلینیک و وضعیت فعال فیلتر شود.",
        tags=["Doctor Clinics"],
        parameters=[
            OpenApiParameter(
                name="doctor_id",
                type=int,
                required=False,
                description="فیلتر بر اساس شناسه پزشک.",
            ),
            OpenApiParameter(
                name="clinic_id",
                type=int,
                required=False,
                description="فیلتر بر اساس شناسه کلینیک.",
            ),
            OpenApiParameter(
                name="is_active",
                type=bool,
                required=False,
                description="فیلتر بر اساس فعال بودن عضویت پزشک در کلینیک.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=DoctorClinicReadSerializer(many=True),
                description="لیست عضویت‌های پزشک-کلینیک با موفقیت دریافت شد.",
            ),
        },
    )
    def get(self, request) -> Response:
        doctor_id = request.query_params.get("doctor_id")
        clinic_id = request.query_params.get("clinic_id")
        is_active = request.query_params.get("is_active")

        doctor_clinics = list_doctor_clinics(
            doctor_id=int(doctor_id) if doctor_id is not None else None,
            clinic_id=int(clinic_id) if clinic_id is not None else None,
            is_active=is_active.lower() == "true" if is_active is not None else None,
        )
        serializer = DoctorClinicReadSerializer(doctor_clinics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="ایجاد ارتباط پزشک و کلینیک",
        description="این API یک ارتباط جدید بین پزشک و کلینیک ایجاد می‌کند تا پزشک بتواند در آن کلینیک فعالیت داشته باشد.",
        tags=["Doctor Clinics"],
        request=DoctorClinicCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=DoctorClinicReadSerializer,
                description="ارتباط پزشک و کلینیک با موفقیت ایجاد شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است."),
        },
    )
    def post(self, request) -> Response:
        serializer = DoctorClinicCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = {
            "doctor_id": serializer.validated_data["doctor"].id,
            "clinic_id": serializer.validated_data["clinic"].id,
            "is_active": serializer.validated_data.get("is_active", True),
        }

        doctor_clinic = create_doctor_clinic(data=data)
        response_serializer = DoctorClinicReadSerializer(doctor_clinic)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DoctorClinicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت جزئیات عضویت پزشک در کلینیک",
        description="این API اطلاعات یک رکورد عضویت پزشک در کلینیک را بر اساس شناسه آن برمی‌گرداند.",
        tags=["Doctor Clinics"],
        responses={
            200: OpenApiResponse(
                response=DoctorClinicReadSerializer,
                description="جزئیات عضویت با موفقیت دریافت شد.",
            ),
            404: OpenApiResponse(description="رکورد عضویت موردنظر پیدا نشد."),
        },
    )
    def get(self, request, doctor_clinic_id: int) -> Response:
        try:
            doctor_clinic = get_doctor_clinic(doctor_clinic_id=doctor_clinic_id)
        except DoctorClinicReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorClinicReadSerializer(doctor_clinic)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="به‌روزرسانی عضویت پزشک در کلینیک",
        description="این API برای تغییر وضعیت فعال بودن ارتباط پزشک و کلینیک استفاده می‌شود.",
        tags=["Doctor Clinics"],
        request=DoctorClinicUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=DoctorClinicReadSerializer,
                description="عضویت پزشک در کلینیک با موفقیت به‌روزرسانی شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است."),
            404: OpenApiResponse(description="رکورد عضویت موردنظر پیدا نشد."),
        },
    )
    def patch(self, request, doctor_clinic_id: int) -> Response:
        try:
            doctor_clinic = get_doctor_clinic(doctor_clinic_id=doctor_clinic_id)
        except DoctorClinicReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorClinicUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        doctor_clinic = update_doctor_clinic(
            doctor_clinic=doctor_clinic,
            is_active=serializer.validated_data.get("is_active"),
        )
        response_serializer = DoctorClinicReadSerializer(doctor_clinic)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class DoctorScheduleListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsDoctorOwner]

    @extend_schema(
        summary="دریافت لیست برنامه‌های کاری پزشکان",
        description="این API برنامه‌های کاری پزشکان را برمی‌گرداند و می‌تواند بر اساس پزشک، کلینیک، روز هفته و وضعیت فعال فیلتر شود.",
        tags=["Doctor Schedules"],
        parameters=[
            OpenApiParameter(
                name="doctor_id",
                type=int,
                required=False,
                description="فیلتر بر اساس شناسه پزشک.",
            ),
            OpenApiParameter(
                name="clinic_id",
                type=int,
                required=False,
                description="فیلتر بر اساس شناسه کلینیک.",
            ),
            OpenApiParameter(
                name="weekday",
                type=int,
                required=False,
                description="فیلتر بر اساس روز هفته از 0 تا 6.",
            ),
            OpenApiParameter(
                name="is_active",
                type=bool,
                required=False,
                description="فیلتر بر اساس فعال بودن برنامه کاری.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=DoctorScheduleReadSerializer(many=True),
                description="لیست برنامه‌های کاری با موفقیت دریافت شد.",
            ),
        },
    )
    def get(self, request) -> Response:
        doctor_id = request.query_params.get("doctor_id")
        clinic_id = request.query_params.get("clinic_id")
        weekday = request.query_params.get("weekday")
        is_active = request.query_params.get("is_active")

        doctor_schedules = list_doctor_schedules(
            doctor_id=int(doctor_id) if doctor_id is not None else None,
            clinic_id=int(clinic_id) if clinic_id is not None else None,
            weekday=int(weekday) if weekday is not None else None,
            is_active=is_active.lower() == "true" if is_active is not None else None,
        )
        serializer = DoctorScheduleReadSerializer(doctor_schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="ایجاد برنامه کاری پزشک",
        description="این API برای ثبت برنامه کاری پزشک در یک کلینیک مشخص با روز هفته، بازه زمانی و مدت هر اسلات استفاده می‌شود.",
        tags=["Doctor Schedules"],
        request=DoctorScheduleCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=DoctorScheduleReadSerializer,
                description="برنامه کاری پزشک با موفقیت ایجاد شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است یا با قوانین زمان‌بندی سازگار نیست."),
        },
    )
    def post(self, request) -> Response:
        serializer = DoctorScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_doctor = serializer.validated_data["doctor"]

        try:
            user_doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            user_doctor = None

        if user_doctor is not None:
            doctor = user_doctor
        else:
            doctor = requested_doctor

        data = {
            "doctor_id": doctor.id,
            "clinic_id": serializer.validated_data["clinic"].id,
            "weekday": serializer.validated_data["weekday"],
            "start_time": serializer.validated_data["start_time"],
            "end_time": serializer.validated_data["end_time"],
            "slot_duration_minutes": serializer.validated_data["slot_duration_minutes"],
            "is_active": serializer.validated_data.get("is_active", True),
        }

        try:
            doctor_schedule = create_doctor_schedule(data=data)
        except ValidationError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = DoctorScheduleReadSerializer(doctor_schedule)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DoctorScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsDoctorOwner]

    @extend_schema(
        summary="دریافت جزئیات برنامه کاری پزشک",
        description="این API جزئیات یک برنامه کاری مشخص را بر اساس شناسه آن برمی‌گرداند.",
        tags=["Doctor Schedules"],
        responses={
            200: OpenApiResponse(
                response=DoctorScheduleReadSerializer,
                description="جزئیات برنامه کاری با موفقیت دریافت شد.",
            ),
            404: OpenApiResponse(description="برنامه کاری موردنظر پیدا نشد."),
        },
    )
    def get(self, request, doctor_schedule_id: int) -> Response:
        try:
            doctor_schedule = get_doctor_schedule(doctor_schedule_id=doctor_schedule_id)
        except DoctorScheduleReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, doctor_schedule)

        serializer = DoctorScheduleReadSerializer(doctor_schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="به‌روزرسانی برنامه کاری پزشک",
        description="این API برای ویرایش روز هفته، ساعت شروع، ساعت پایان، مدت هر اسلات و وضعیت فعال بودن برنامه کاری استفاده می‌شود.",
        tags=["Doctor Schedules"],
        request=DoctorScheduleUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=DoctorScheduleReadSerializer,
                description="برنامه کاری با موفقیت به‌روزرسانی شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است یا با قوانین زمان‌بندی سازگار نیست."),
            404: OpenApiResponse(description="برنامه کاری موردنظر پیدا نشد."),
        },
    )
    def patch(self, request, doctor_schedule_id: int) -> Response:
        try:
            doctor_schedule = get_doctor_schedule(doctor_schedule_id=doctor_schedule_id)
        except DoctorScheduleReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, doctor_schedule)

        serializer = DoctorScheduleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            doctor_schedule = update_doctor_schedule(
                doctor_schedule=doctor_schedule,
                weekday=serializer.validated_data.get("weekday"),
                start_time=serializer.validated_data.get("start_time"),
                end_time=serializer.validated_data.get("end_time"),
                slot_duration_minutes=serializer.validated_data.get(
                    "slot_duration_minutes"
                ),
                is_active=serializer.validated_data.get("is_active"),
            )
        except ValidationError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = DoctorScheduleReadSerializer(doctor_schedule)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="غیرفعال‌سازی برنامه کاری پزشک",
        description="این API برنامه کاری پزشک را به صورت نرم غیرفعال می‌کند تا دیگر برای رزرو نوبت استفاده نشود.",
        tags=["Doctor Schedules"],
        responses={
            200: OpenApiResponse(
                response=DoctorScheduleReadSerializer,
                description="برنامه کاری با موفقیت غیرفعال شد.",
            ),
            404: OpenApiResponse(description="برنامه کاری موردنظر پیدا نشد."),
        },
    )
    def delete(self, request, doctor_schedule_id: int) -> Response:
        try:
            doctor_schedule = get_doctor_schedule(doctor_schedule_id=doctor_schedule_id)
        except DoctorScheduleReadSerializer.Meta.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, doctor_schedule)

        doctor_schedule = deactivate_doctor_schedule(doctor_schedule=doctor_schedule)
        response_serializer = DoctorScheduleReadSerializer(doctor_schedule)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
