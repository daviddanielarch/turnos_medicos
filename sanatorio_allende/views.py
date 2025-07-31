import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import (
    AppointmentType,
    BestAppointmentFound,
    DeviceRegistration,
    Doctor,
    FindAppointment,
)


class LoginView(View):
    """View to serve the Auth0 login template"""

    def get(self, request):
        """Render the login template with Auth0 configuration"""
        context = {
            "auth0_domain": settings.AUTH0_DOMAIN,
            "auth0_client_id": getattr(settings, "AUTH0_CLIENT_ID", ""),
            "auth0_audience": settings.AUTH0_AUDIENCE,
        }
        return render(request, "login.html", context)


@method_decorator(csrf_exempt, name="dispatch")
class AuthCallbackView(View):
    """Handle Auth0 callback (redirects back to login page)"""

    def get(self, request):
        """Redirect to login page after Auth0 callback"""
        return render(
            request,
            "login.html",
            {
                "auth0_domain": settings.AUTH0_DOMAIN,
                "auth0_client_id": getattr(settings, "AUTH0_CLIENT_ID", ""),
                "auth0_audience": settings.AUTH0_AUDIENCE,
            },
        )


@method_decorator(csrf_exempt, name="dispatch")
class DoctorListView(LoginRequiredMixin, View):
    """Class-based view for listing doctors"""

    def get(self, request):
        """Get all doctors with their specialties and locations"""
        doctors = Doctor.objects.select_related("especialidad").all()

        doctors_data = []
        for doctor in doctors:
            doctors_data.append(
                {
                    "id": doctor.id,
                    "name": doctor.name,
                    "especialidad": doctor.especialidad.name,
                    "location": doctor.especialidad.sucursal,
                }
            )

        return JsonResponse({"success": True, "doctors": doctors_data})


@method_decorator(csrf_exempt, name="dispatch")
class AppointmentTypeListView(LoginRequiredMixin, View):
    """Class-based view for listing appointment types for a specific doctor"""

    def get(self, request):
        """Get appointment types for a specific doctor"""
        doctor_id = request.GET.get("doctor_id")
        if not doctor_id:
            return JsonResponse(
                {"success": False, "error": "doctor_id parameter is required"},
                status=400,
            )

        doctor = get_object_or_404(Doctor, id=doctor_id)
        appointment_types = AppointmentType.objects.filter(
            especialidad=doctor.especialidad
        )

        types_data = []
        for apt_type in appointment_types:
            types_data.append(
                {
                    "id": apt_type.id,
                    "name": apt_type.name,
                    "description": f"{apt_type.name} appointment",
                    "id_tipo_turno": apt_type.id_tipo_turno,
                }
            )

        return JsonResponse({"success": True, "appointment_types": types_data})


@method_decorator(csrf_exempt, name="dispatch")
class FindAppointmentView(LoginRequiredMixin, View):
    """Class-based view for FindAppointment CRUD operations"""

    def get(self, request):
        """Get all FindAppointment objects with optional time filtering"""
        # Get optional seconds parameter for filtering recent appointments
        seconds_filter = request.GET.get("seconds")

        find_appointments = FindAppointment.objects.select_related(
            "doctor",
            "doctor__especialidad",
            "tipo_de_turno",
        )

        # If seconds parameter is provided, filter by recent appointments
        if seconds_filter:
            try:
                seconds = int(seconds_filter)
                time_threshold = timezone.now() - timedelta(seconds=seconds)

                # Get recent best appointments found within the time window
                recent_best_appointments = BestAppointmentFound.objects.filter(
                    datetime__gte=time_threshold
                ).values_list("appointment_wanted_id", flat=True)

                # Filter find appointments that have recent best appointments
                find_appointments = find_appointments.filter(
                    id__in=recent_best_appointments
                )
            except ValueError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Invalid seconds parameter. Must be a number.",
                    },
                    status=400,
                )

        appointments_data = []
        for appointment in find_appointments:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "doctor": {
                        "id": appointment.doctor.id,
                        "name": appointment.doctor.name,
                        "especialidad": appointment.doctor.especialidad.name,
                        "location": appointment.doctor.especialidad.sucursal,
                    },
                    "tipo_de_turno": {
                        "id": appointment.tipo_de_turno.id,
                        "name": appointment.tipo_de_turno.name,
                    },
                    "is_active": appointment.is_active,
                    "created_at": appointment.created_at.isoformat(),
                    "updated_at": appointment.updated_at.isoformat(),
                }
            )

        return JsonResponse({"success": True, "appointments": appointments_data})

    def post(self, request):
        """Create a new FindAppointment"""
        data = json.loads(request.body)
        doctor_id = data.get("doctor_id")
        tipo_de_turno_id = data.get("tipo_de_turno_id")

        if not doctor_id or not tipo_de_turno_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "doctor_id and tipo_de_turno_id are required",
                },
                status=400,
            )

        try:
            doctor = Doctor.objects.get(id=doctor_id)
            tipo_de_turno = AppointmentType.objects.get(id=tipo_de_turno_id)

            appointment = FindAppointment.objects.create(
                doctor=doctor,
                tipo_de_turno=tipo_de_turno,
                is_active=True,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Appointment search created successfully",
                    "appointment": {
                        "id": appointment.id,
                        "doctor": {
                            "id": appointment.doctor.id,
                            "name": appointment.doctor.name,
                            "especialidad": appointment.doctor.especialidad.name,
                            "location": appointment.doctor.especialidad.sucursal,
                        },
                        "tipo_de_turno": {
                            "id": appointment.tipo_de_turno.id,
                            "name": appointment.tipo_de_turno.name,
                        },
                        "is_active": appointment.is_active,
                        "created_at": appointment.created_at.isoformat(),
                        "updated_at": appointment.updated_at.isoformat(),
                    },
                },
                status=201,
            )
        except (Doctor.DoesNotExist, AppointmentType.DoesNotExist):
            return JsonResponse(
                {"success": False, "error": "Invalid doctor_id or tipo_de_turno_id"},
                status=400,
            )

    def patch(self, request):
        """Update the active status of a FindAppointment"""
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        is_active = data.get("is_active")

        if appointment_id is None or is_active is None:
            return JsonResponse(
                {
                    "success": False,
                    "error": "appointment_id and is_active are required",
                },
                status=400,
            )

        try:
            appointment = FindAppointment.objects.get(id=appointment_id)
            appointment.is_active = is_active
            appointment.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Appointment status updated successfully",
                    "appointment": {
                        "id": appointment.id,
                        "is_active": appointment.is_active,
                        "updated_at": appointment.updated_at.isoformat(),
                    },
                }
            )
        except FindAppointment.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Appointment not found"}, status=404
            )


@method_decorator(csrf_exempt, name="dispatch")
class BestAppointmentListView(LoginRequiredMixin, View):
    """Class-based view for listing best appointments found"""

    def get(self, request):
        """Get all best appointments found"""
        best_appointments = BestAppointmentFound.objects.select_related(
            "appointment_wanted__doctor",
            "appointment_wanted__doctor__especialidad",
            "appointment_wanted__tipo_de_turno",
        ).order_by("-datetime")

        appointments_data = []
        for appointment in best_appointments:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "doctor_name": appointment.appointment_wanted.doctor.name,
                    "especialidad": appointment.appointment_wanted.doctor.especialidad.name,
                    "location": appointment.appointment_wanted.doctor.especialidad.sucursal,
                    "tipo_de_turno": appointment.appointment_wanted.tipo_de_turno.name,
                    "best_datetime": appointment.datetime.isoformat(),
                }
            )

        return JsonResponse({"success": True, "best_appointments": appointments_data})


@method_decorator(csrf_exempt, name="dispatch")
class DeviceRegistrationView(LoginRequiredMixin, View):
    """Class-based view for DeviceRegistration operations"""

    def post(self, request):
        """Register or update a device for push notifications"""
        data = json.loads(request.body)
        push_token = data.get("push_token")
        platform = data.get("platform", "expo")

        if not push_token:
            return JsonResponse(
                {"success": False, "error": "push_token is required"},
                status=400,
            )

        # Check if device is already registered
        device, created = DeviceRegistration.objects.get_or_create(
            push_token=push_token,
            defaults={
                "platform": platform,
                "is_active": True,
            },
        )

        if not created:
            # Update existing device
            device.platform = platform
            device.is_active = True
            device.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Device registered successfully",
                "created": created,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class HealthCheckView(LoginRequiredMixin, View):
    """Health check endpoint that doesn't require authentication"""

    def get(self, request):
        """Simple health check endpoint"""
        return JsonResponse(
            {
                "success": True,
                "status": "healthy",
                "timestamp": timezone.now().isoformat(),
                "message": "API is running",
            }
        )
