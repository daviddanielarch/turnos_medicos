from django import forms
from django.contrib import admin

from .models import (
    BestAppointmentFound,
    DeviceRegistration,
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
