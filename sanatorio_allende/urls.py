from django.urls import path

from . import views

app_name = "sanatorio_allende"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("auth/callback/", views.AuthCallbackView.as_view(), name="auth_callback"),
    path("api/doctors/", views.DoctorListView.as_view(), name="api_doctors"),
    path(
        "api/appointment-types/",
        views.AppointmentTypeListView.as_view(),
        name="api_appointment_types",
    ),
    path(
        "api/patients/",
        views.PatientListView.as_view(),
        name="api_patients",
    ),
    path(
        "api/find-appointments/",
        views.FindAppointmentView.as_view(),
        name="api_find_appointments",
    ),
    path(
        "api/best-appointments/",
        views.BestAppointmentListView.as_view(),
        name="api_best_appointments",
    ),
    path(
        "api/appointment/",
        views.AppointmentView.as_view(),
        name="api_appointment",
    ),
    path(
        "api/device-registrations/",
        views.DeviceRegistrationView.as_view(),
        name="api_register_device",
    ),
]
