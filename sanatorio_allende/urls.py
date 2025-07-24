from django.urls import path

from . import views

app_name = "sanatorio_allende"

urlpatterns = [
    path("api/doctors/", views.api_doctors, name="api_doctors"),
    path(
        "api/appointment-types/",
        views.api_appointment_types,
        name="api_appointment_types",
    ),
    path(
        "api/create-appointment/",
        views.api_create_appointment,
        name="api_create_appointment",
    ),
    path(
        "api/find-appointments/",
        views.api_find_appointments,
        name="api_find_appointments",
    ),
    path(
        "api/update-appointment-status/",
        views.api_update_appointment_status,
        name="api_update_appointment_status",
    ),
    path(
        "api/best-appointments/",
        views.api_best_appointments,
        name="api_best_appointments",
    ),
]
