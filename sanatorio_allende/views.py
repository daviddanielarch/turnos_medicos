import json

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from sanatorio_allende.allende_api import Allende, UnauthorizedException

from .models import (
    BestAppointmentFound,
    DeviceRegistration,
    FindAppointment,
    PacienteAllende,
)


class LoginView(View):
    """View to serve the Auth0 login template"""

    def get(self, request: HttpRequest) -> HttpResponse:
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

    def get(self, request: HttpRequest) -> HttpResponse:
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

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get all doctors with their specialties and locations"""
        pattern = request.GET.get("pattern", "")
        patient_id = request.GET.get("patient_id")
        patient = get_object_or_404(PacienteAllende, id=patient_id)
        if patient.user != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient does not belong to the current user",
                },
                status=401,
            )
        allende = Allende(auth_header=patient.token)
        try:
            doctors = allende.get_doctors(pattern=pattern)
            return JsonResponse({"success": True, "doctors": doctors})
        except UnauthorizedException:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Unauthorized - please re-authenticate",
                },
                status=401,
            )
        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Network error - please try again later",
                },
                status=503,
            )


@method_decorator(csrf_exempt, name="dispatch")
class AppointmentTypeListView(LoginRequiredMixin, View):
    """Class-based view for listing appointment types for a specific doctor"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get appointment types for a specific doctor"""
        patient_id = request.GET.get("patient_id")
        patient = get_object_or_404(PacienteAllende, id=patient_id)
        if patient.user != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient does not belong to the current user",
                },
                status=401,
            )

        allende = Allende(auth_header=patient.token)
        if (
            not request.GET.get("id_especialidad")
            or not request.GET.get("id_servicio")
            or not request.GET.get("id_sucursal")
        ):
            return JsonResponse(
                {
                    "success": False,
                    "error": "id_especialidad, id_servicio, and id_sucursal are required",
                },
                status=400,
            )
        id_especialidad = request.GET["id_especialidad"]
        id_servicio = request.GET["id_servicio"]
        id_sucursal = request.GET["id_sucursal"]

        try:
            appointment_types = allende.get_available_appointment_types(
                id_especialidad=id_especialidad,
                id_servicio=id_servicio,
                id_sucursal=id_sucursal,
            )
            return JsonResponse(
                {"success": True, "appointment_types": appointment_types}
            )
        except UnauthorizedException:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Unauthorized - please re-authenticate",
                },
                status=401,
            )
        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Network error - please try again later",
                },
                status=503,
            )


@method_decorator(csrf_exempt, name="dispatch")
class FindAppointmentView(LoginRequiredMixin, View):
    """Class-based view for FindAppointment CRUD operations"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get all FindAppointment objects with optional time filtering"""
        # Get optional seconds parameter for filtering recent appointments
        patient_id = request.GET.get("patient_id")
        patient = get_object_or_404(PacienteAllende, id=patient_id)
        if patient.user != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient does not belong to the current user",
                },
                status=401,
            )

        find_appointments = FindAppointment.objects.filter(patient=patient)

        appointments_data = []
        for appointment in find_appointments:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "name": appointment.doctor_name,
                    "especialidad": appointment.especialidad,
                    "location": appointment.sucursal,
                    "enabled": appointment.active,
                    "tipo_de_turno": appointment.nombre_tipo_prestacion,
                    "doctor_id": appointment.id_recurso,
                    "tipo_de_turno_id": appointment.id_tipo_prestacion,
                    "desired_timeframe": appointment.desired_timeframe,
                }
            )

        return JsonResponse({"success": True, "appointments": appointments_data})

    def post(self, request: HttpRequest) -> JsonResponse:
        """Create a new FindAppointment"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )
        id_servicio = data.get("id_servicio")
        id_sucursal = data.get("id_sucursal")
        id_recurso = data.get("id_recurso")
        id_especialidad = data.get("id_especialidad")
        id_tipo_recurso = data.get("id_tipo_recurso")
        id_prestacion = data.get("id_prestacion")
        id_tipo_prestacion = data.get("id_tipo_prestacion")
        nombre_tipo_prestacion = data.get("nombre_tipo_prestacion")

        if (
            not id_servicio
            or not id_sucursal
            or not id_recurso
            or not id_especialidad
            or not id_tipo_recurso
            or not id_prestacion
            or not id_tipo_prestacion
            or not nombre_tipo_prestacion
        ):
            return JsonResponse(
                {
                    "success": False,
                    "error": "id_servicio, id_sucursal, id_recurso, id_especialidad, id_tipo_recurso, id_prestacion, id_tipo_prestacion, and nombre_tipo_prestacion are required",
                },
                status=400,
            )

        patient_id = data.get("patient_id")
        patient = get_object_or_404(PacienteAllende, id=patient_id)

        doctor_name = data.get("doctor_name")
        servicio = data.get("servicio")
        sucursal = data.get("sucursal")
        especialidad = data.get("especialidad")
        desired_timeframe = data.get(
            "desired_timeframe", FindAppointment.DEFAULT_DESIRED_TIMEFRAME
        )

        patient = get_object_or_404(PacienteAllende, id=patient_id)
        if patient.user != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient does not belong to the current user",
                },
                status=401,
            )

        existing_appointment = FindAppointment.objects.filter(
            patient=patient,
            id_servicio=id_servicio,
            id_sucursal=id_sucursal,
            id_recurso=id_recurso,
            id_especialidad=id_especialidad,
        ).first()

        if existing_appointment:
            existing_appointment.desired_timeframe = desired_timeframe
            existing_appointment.save(update_fields=["desired_timeframe"])
            return JsonResponse(
                {"success": True, "message": "Appointment updated successfully"}
            )

        # Create new appointment
        appointment = FindAppointment.objects.create(
            doctor_name=doctor_name,
            id_servicio=id_servicio,
            servicio=servicio,
            id_sucursal=id_sucursal,
            sucursal=sucursal,
            id_especialidad=id_especialidad,
            especialidad=especialidad,
            id_recurso=id_recurso,
            id_tipo_recurso=id_tipo_recurso,
            id_prestacion=id_prestacion,
            id_tipo_prestacion=id_tipo_prestacion,
            nombre_tipo_prestacion=nombre_tipo_prestacion,
            patient=patient,
            active=True,
            desired_timeframe=desired_timeframe,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Appointment created successfully",
                "appointment_id": appointment.id,
            }
        )

    def patch(self, request: HttpRequest) -> JsonResponse:
        """Update the active status of a FindAppointment"""
        assert isinstance(request.user, User)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )
        appointment_id = data.get("appointment_id")
        active = data.get("active")

        if appointment_id is None or active is None:
            return JsonResponse(
                {
                    "success": False,
                    "error": "appointment_id and active parameters are required",
                },
                status=400,
            )

        appointment = get_object_or_404(FindAppointment, id=appointment_id)
        user_patients = request.user.pacienteallende_set.all().values_list(
            "id", flat=True
        )
        if appointment.patient.id not in user_patients:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Appointment does not belong to the current user",
                },
                status=401,
            )
        appointment.active = active
        appointment.save(update_fields=["active"])

        return JsonResponse(
            {
                "success": True,
                "message": f'Appointment status updated to {"active" if active else "inactive"}',
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class BestAppointmentListView(LoginRequiredMixin, View):
    """Class-based view for listing BestAppointmentFound objects"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get all BestAppointmentFound objects (excluding not_interested ones)"""
        patient_id = request.GET.get("patient_id")
        patient = get_object_or_404(PacienteAllende, id=patient_id)
        if patient.user != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient does not belong to the current user",
                },
                status=401,
            )

        best_appointments = BestAppointmentFound.objects.select_related(
            "appointment_wanted",
        ).filter(patient=patient, not_interested=False, datetime__gte=timezone.now())

        appointments_data = []
        for best_appointment in best_appointments:
            appointment = best_appointment.appointment_wanted
            appointments_data.append(
                {
                    "id": best_appointment.id,
                    "doctor_name": appointment.doctor_name,
                    "especialidad": appointment.especialidad,
                    "location": appointment.sucursal,
                    "tipo_de_turno": appointment.nombre_tipo_prestacion,
                    "best_datetime": best_appointment.datetime.isoformat(),
                    "duracion_individual": best_appointment.duracion_individual,
                    "id_plantilla_turno": best_appointment.id_plantilla_turno,
                    "id_item_plantilla": best_appointment.id_item_plantilla,
                    "confirmed": best_appointment.confirmed,
                    "confirmed_at": (
                        best_appointment.confirmed_at.isoformat()
                        if best_appointment.confirmed_at
                        else None
                    ),
                }
            )

        return JsonResponse({"success": True, "best_appointments": appointments_data})

    def patch(self, request: HttpRequest) -> JsonResponse:
        """Mark an appointment as not interested"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )
        appointment_id = data.get("appointment_id")
        not_interested = data.get("not_interested", True)

        if appointment_id is None:
            return JsonResponse(
                {
                    "success": False,
                    "error": "appointment_id is required",
                },
                status=400,
            )

        try:
            best_appointment = BestAppointmentFound.objects.get(id=appointment_id)
            if best_appointment.patient.user != request.user:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Appointment does not belong to the current user",
                    },
                    status=401,
                )

            best_appointment.not_interested = not_interested
            best_appointment.save(update_fields=["not_interested"])

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Appointment marked as {'not interested' if not_interested else 'interested'}",
                }
            )
        except BestAppointmentFound.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Appointment not found",
                },
                status=404,
            )


@method_decorator(csrf_exempt, name="dispatch")
class PatientListView(LoginRequiredMixin, View):
    """Class-based view for listing patients"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get all patients"""
        assert isinstance(request.user, User)
        patients = PacienteAllende.objects.filter(user=request.user)

        patients_data = []
        for patient in patients:
            patients_data.append(
                {
                    "id": patient.id,
                    "name": patient.name,
                    "id_paciente": patient.id_paciente,
                    "docid": patient.docid,
                    "updated_at": (
                        patient.updated_at.isoformat() if patient.updated_at else None
                    ),
                }
            )

        return JsonResponse({"success": True, "patients": patients_data})

    def post(self, request: HttpRequest) -> JsonResponse:
        """Create a new patient"""
        assert isinstance(request.user, User)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )
        name = data.get("name")
        docid = data.get("docid")
        password = data.get("password")

        if not name or not docid or not password:
            return JsonResponse(
                {
                    "success": False,
                    "error": "name, docid, and password are required",
                },
                status=400,
            )

        if not Allende.validate_credentials(dni=docid, password=password):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid credentials",
                },
                status=400,
            )

        # Check if patient already exists with the same docid
        existing_patient = PacienteAllende.objects.filter(docid=docid).first()
        if existing_patient:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient already exists with this document ID",
                },
                status=400,
            )

        patient = PacienteAllende.objects.create(
            user=request.user,
            name=name,
            docid=docid,
            password=password,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Patient created successfully",
                "patient_id": patient.id,
            }
        )

    def delete(self, request: HttpRequest) -> JsonResponse:
        """Delete a patient"""
        assert isinstance(request.user, User)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )
        patient_id = data.get("patient_id")

        if not patient_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "patient_id is required",
                },
                status=400,
            )

        try:
            patient = PacienteAllende.objects.get(id=patient_id, user=request.user)
            patient.delete()
            return JsonResponse(
                {
                    "success": True,
                    "message": "Patient deleted successfully",
                }
            )
        except PacienteAllende.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Patient not found",
                },
                status=404,
            )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceRegistrationView(LoginRequiredMixin, View):
    """Class-based view for DeviceRegistration operations"""

    def post(self, request: HttpRequest) -> JsonResponse:
        """Register or update a device for push notifications"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )
        push_token = data.get("push_token")
        platform = data.get("platform", "expo")

        if not push_token:
            return JsonResponse(
                {"success": False, "error": "push_token is required"},
                status=400,
            )

        device, created = DeviceRegistration.objects.get_or_create(
            push_token=push_token,
            defaults={
                "platform": platform,
                "is_active": True,
                "user": request.user,
            },
        )

        if not created:
            device.platform = platform
            device.is_active = True
            device.save(update_fields=["platform", "is_active"])

        return JsonResponse(
            {
                "success": True,
                "message": "Device registered successfully",
                "created": created,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class AppointmentView(LoginRequiredMixin, View):
    """Class-based view for confirming appointments"""

    def post(self, request: HttpRequest) -> JsonResponse:
        """Confirm an appointment by calling the Allende reservar endpoint"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )

        appointment_id = data.get("appointment_id")
        appointment = get_object_or_404(BestAppointmentFound, id=appointment_id)

        if appointment.confirmed:
            return JsonResponse(
                {"success": False, "error": "Appointment is already confirmed"},
                status=400,
            )

        patient = appointment.patient
        assert isinstance(patient.id_paciente, str)
        assert isinstance(patient.id_financiador, int)
        assert isinstance(patient.id_plan, int)
        allende = Allende(auth_header=patient.token)

        appointment_data = {
            "CriterioBusquedaDto": {
                "IdPaciente": int(patient.id_paciente),
                "IdServicio": appointment.appointment_wanted.id_servicio,
                "IdSucursal": appointment.appointment_wanted.id_sucursal,
                "IdRecurso": appointment.appointment_wanted.id_recurso,
                "IdEspecialidad": appointment.appointment_wanted.id_especialidad,
                "ControlarEdad": False,
                "IdTipoDeTurno": appointment.appointment_wanted.id_tipo_prestacion,
                "IdFinanciador": int(patient.id_financiador),
                "IdTipoRecurso": appointment.appointment_wanted.id_tipo_recurso,
                "IdPlan": int(patient.id_plan),
                "Prestaciones": [
                    {
                        "IdPrestacion": appointment.appointment_wanted.id_prestacion,
                        "IdItemSolicitudEstudios": 0,
                    }
                ],
            },
            "TurnoElegidoDto": {
                "Fecha": timezone.localtime(appointment.datetime).strftime(
                    "%Y-%m-%dT00:00:00"
                ),
                "Hora": timezone.localtime(appointment.datetime).strftime("%H:%M"),
                "IdItemDePlantilla": appointment.id_item_plantilla,
                "IdPlantillaTurno": appointment.id_plantilla_turno,
                "IdSucursal": appointment.appointment_wanted.id_sucursal,
                "DuracionIndividual": appointment.duracion_individual,
                "RequisitoAdministrativoAlOtorgar": "DNI\nCredencial Financiador\n AUTORIZACION: Con autorización online",
            },
            "Observaciones": None,
        }

        try:
            result = allende.book_appointment(appointment_data)
            if result.id_turno is None:
                print(result.data)
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No se pudo obtener el ID del turno",
                    },
                    status=400,
                )

            appointment.confirmed_id_turno = result.id_turno
            appointment.confirmed = True
            appointment.confirmed_at = timezone.now()
            appointment.save()

            return JsonResponse(
                {"success": True, "message": "Appointment confirmed successfully"}
            )

        except UnauthorizedException:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Unauthorized - please re-authenticate",
                },
                status=401,
            )
        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Network error - please try again later",
                },
                status=503,
            )

    def delete(self, request: HttpRequest) -> JsonResponse:
        """Cancel an appointment by calling the Allende cancel_appointment endpoint"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )

        appointment_id = data.get("appointment_id")
        appointment = get_object_or_404(BestAppointmentFound, id=appointment_id)

        if not appointment.confirmed:
            return JsonResponse(
                {"success": False, "error": "Appointment is not confirmed"},
                status=400,
            )

        patient = appointment.patient
        assert isinstance(patient.id_paciente, str)
        assert isinstance(patient.id_financiador, int)
        assert isinstance(patient.id_plan, int)
        assert isinstance(appointment.confirmed_id_turno, int)
        allende = Allende(auth_header=patient.token)

        try:
            response = allende.cancel_appointment(appointment.confirmed_id_turno)
            if not response.IsOk:
                return JsonResponse(
                    {"success": False, "error": response.Message},
                    status=400,
                )

            appointment.confirmed = False
            appointment.confirmed_id_turno = None
            appointment.confirmed_at = None
            appointment.save()

            return JsonResponse(
                {"success": True, "message": "Appointment cancelled successfully"}
            )
        except UnauthorizedException:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Unauthorized - please re-authenticate",
                },
                status=401,
            )
        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Network error - please try again later",
                },
                status=503,
            )
