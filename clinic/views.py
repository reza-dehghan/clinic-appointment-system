from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from clinic import selectors, services
from clinic.serializers import (
    ClinicCreateSerializer,
    ClinicReadSerializer,
    ClinicUpdateSerializer,
)


class ClinicListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت لیست کلینیک‌ها",
        description="این API فهرست کلینیک‌های ثبت‌شده را برای کاربران احراز هویت‌شده برمی‌گرداند.",
        tags=["Clinics"],
        responses={
            200: OpenApiResponse(
                response=ClinicReadSerializer(many=True),
                description="لیست کلینیک‌ها با موفقیت دریافت شد.",
            ),
        },
    )
    def get(self, request) -> Response:
        clinics = selectors.list_clinics()
        serializer = ClinicReadSerializer(clinics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="ایجاد کلینیک جدید",
        description="این API یک کلینیک جدید را با اطلاعات پایه مانند نام، کد، آدرس و اطلاعات تماس ایجاد می‌کند.",
        tags=["Clinics"],
        request=ClinicCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=ClinicReadSerializer,
                description="کلینیک با موفقیت ایجاد شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است."),
        },
    )
    def post(self, request) -> Response:
        serializer = ClinicCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clinic = services.create_clinic(**serializer.validated_data)

        response_serializer = ClinicReadSerializer(clinic)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ClinicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="دریافت جزئیات کلینیک",
        description="این API اطلاعات کامل یک کلینیک را بر اساس شناسه آن برمی‌گرداند.",
        tags=["Clinics"],
        responses={
            200: OpenApiResponse(
                response=ClinicReadSerializer,
                description="اطلاعات کلینیک با موفقیت دریافت شد.",
            ),
            404: OpenApiResponse(description="کلینیک موردنظر پیدا نشد."),
        },
    )
    def get(self, request, clinic_id: int) -> Response:
        try:
            clinic = selectors.get_clinic_by_id(clinic_id)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ClinicReadSerializer(clinic)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="به‌روزرسانی کلینیک",
        description="این API برای ویرایش بخشی از اطلاعات کلینیک مانند نام، آدرس، شماره تماس یا منطقه زمانی استفاده می‌شود.",
        tags=["Clinics"],
        request=ClinicUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=ClinicReadSerializer,
                description="اطلاعات کلینیک با موفقیت به‌روزرسانی شد.",
            ),
            400: OpenApiResponse(description="داده‌های ورودی نامعتبر است."),
            404: OpenApiResponse(description="کلینیک موردنظر پیدا نشد."),
        },
    )
    def patch(self, request, clinic_id: int) -> Response:
        try:
            clinic = selectors.get_clinic_by_id(clinic_id)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ClinicUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        clinic = services.update_clinic(clinic, **serializer.validated_data)

        response_serializer = ClinicReadSerializer(clinic)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
