from django import forms
from django.contrib import admin, messages
from django.db.models import Q, QuerySet
from django.http import HttpRequest, JsonResponse
from django.urls import path

from sanatorio_allende.services.data_loader import DataLoader

from .models import (
    AppointmentType,
    BestAppointmentFound,
    DeviceRegistration,
    Doctor,
    Especialidad,
    FindAppointment,
    PacienteAllende,
)


class FindAppointmentAdminForm(forms.ModelForm):
    class Meta:
        model = FindAppointment
        fields = "__all__"

    class Media:
        js = ("admin/js/find_appointment_filter.js",)


@admin.register(FindAppointment)
class FindAppointmentAdmin(admin.ModelAdmin):
    form = FindAppointmentAdminForm
    list_display = ["doctor_name", "nombre_tipo_prestacion", "active"]
    list_filter = ["doctor_name", "nombre_tipo_prestacion", "active"]
    search_fields = ["doctor_name"]
    list_editable = ["active"]

    def get_urls(self) -> list:
        urls = super().get_urls()
        custom_urls = [
            path(
                "get-tipos-turno/<int:doctor_id>/",
                self.get_tipos_turno,
                name="get_tipos_turno",
            ),
        ]
        return custom_urls + urls

    def get_tipos_turno(self, request: HttpRequest, doctor_id: int) -> JsonResponse:
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            tipos_turno = AppointmentType.objects.filter(
                especialidad=doctor.especialidad
            )
            data = [{"id": tt.id, "name": tt.name} for tt in tipos_turno]
            return JsonResponse({"tipos_turno": data})
        except Doctor.DoesNotExist:
            return JsonResponse({"tipos_turno": []})


@admin.register(BestAppointmentFound)
class BestAppointmentFoundAdmin(admin.ModelAdmin):
    list_display = ["appointment_wanted", "datetime"]
    list_filter = ["appointment_wanted", "datetime"]
    search_fields = ["appointment_wanted"]


@admin.register(PacienteAllende)
class PacienteAllendeAdmin(admin.ModelAdmin):
    list_display = ["name", "id_paciente", "id_financiador", "id_plan"]
    list_filter = ["id_paciente", "id_financiador", "id_plan"]
    search_fields = ["id_paciente", "name"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "especialidad",
        "id_recurso",
        "id_tipo_recurso",
    ]
    list_filter = ["especialidad"]
    search_fields = ["name"]


@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ["platform", "push_token_short", "is_active", "created_at"]
    list_filter = ["platform", "is_active", "created_at"]
    search_fields = ["push_token"]
    readonly_fields = ["created_at", "updated_at"]
    list_editable = ["is_active"]

    def push_token_short(self, obj: DeviceRegistration) -> str:
        return (
            obj.push_token[:30] + "..." if len(obj.push_token) > 30 else obj.push_token
        )

    push_token_short.short_description = "Push Token"  # type: ignore
