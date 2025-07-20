from django.contrib import admin
from django import forms
from django.urls import path
from django.http import JsonResponse
from django.db.models import Q
from .models import (
    FindAppointment,
    BestAppointmentFound,
    PacienteAllende,
    Doctor,
    TipoDeTurno,
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
    list_display = ["doctor", "tipo_de_turno", "active"]
    list_filter = ["doctor", "tipo_de_turno", "active"]
    search_fields = ["doctor"]
    list_editable = ["active"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "get-tipos-turno/<int:doctor_id>/",
                self.get_tipos_turno,
                name="get_tipos_turno",
            ),
        ]
        return custom_urls + urls

    def get_tipos_turno(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id_recurso=doctor_id)
            tipos_turno = TipoDeTurno.objects.filter(id_servicio=doctor.id_servicio)
            data = [{"id": tt.id_tipo_turno, "name": tt.name} for tt in tipos_turno]
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
    list_display = ["name", "id_paciente"]
    list_filter = ["id_paciente"]
    search_fields = ["id_paciente"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "especialidad",
        "servicio",
        "sucursal",
        "id_recurso",
        "id_tipo_recurso",
        "id_especialidad",
        "id_sucursal",
        "id_servicio",
    ]
    list_filter = ["especialidad", "servicio", "sucursal"]
    search_fields = ["name"]


@admin.register(TipoDeTurno)
class TipoDeTurnoAdmin(admin.ModelAdmin):
    list_display = ["name", "id_tipo_turno", "id_servicio"]
    list_filter = ["id_servicio"]
    search_fields = ["name"]
