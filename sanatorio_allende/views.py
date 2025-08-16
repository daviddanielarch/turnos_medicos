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

from sanatorio_allende.appointments import Allende, UnauthorizedException

from .models import (
    AppointmentType,
    BestAppointmentFound,
    DeviceRegistration,
    Doctor,
    FindAppointment,
    PacienteAllende,
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

        find_appointments = FindAppointment.objects.select_related(
            "doctor",
            "doctor__especialidad",
            "tipo_de_turno",
        ).filter(patient=patient)

        appointments_data = []
        for appointment in find_appointments:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "name": appointment.doctor.name,
                    "especialidad": appointment.doctor.especialidad.name,
                    "location": appointment.doctor.especialidad.sucursal,
                    "enabled": appointment.active,
                    "tipo_de_turno": appointment.tipo_de_turno.name,
                    "doctor_id": appointment.doctor.id,
                    "tipo_de_turno_id": appointment.tipo_de_turno.id,
                    "desired_timeframe": appointment.desired_timeframe,
                }
            )

        return JsonResponse({"success": True, "appointments": appointments_data})

    def post(self, request):
        """Create a new FindAppointment"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )

        doctor_id = data.get("doctor_id")
        appointment_type_id = data.get("appointment_type_id")
        patient_id = data.get("patient_id")
        desired_timeframe = data.get(
            "desired_timeframe", FindAppointment.DEFAULT_DESIRED_TIMEFRAME
        )

        if not doctor_id or not appointment_type_id or not patient_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "doctor_id, appointment_type_id, and patient_id are required",
                },
                status=400,
            )

        doctor = get_object_or_404(Doctor, id=doctor_id)
        appointment_type = get_object_or_404(AppointmentType, id=appointment_type_id)
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
            doctor=doctor, tipo_de_turno=appointment_type, patient=patient
        ).first()

        if existing_appointment:
            existing_appointment.desired_timeframe = desired_timeframe
            existing_appointment.save()
            return JsonResponse(
                {"success": True, "message": "Appointment updated successfully"}
            )

        # Create new appointment
        appointment = FindAppointment.objects.create(
            doctor=doctor,
            tipo_de_turno=appointment_type,
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

    def patch(self, request):
        """Update the active status of a FindAppointment"""
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
        appointment.save()

        return JsonResponse(
            {
                "success": True,
                "message": f'Appointment status updated to {"active" if active else "inactive"}',
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class BestAppointmentListView(LoginRequiredMixin, View):
    """Class-based view for listing BestAppointmentFound objects"""

    def get(self, request):
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
            "appointment_wanted__doctor",
            "appointment_wanted__doctor__especialidad",
            "appointment_wanted__tipo_de_turno",
        ).filter(patient=patient, not_interested=False, datetime__gte=timezone.now())

        appointments_data = []
        for best_appointment in best_appointments:
            appointment = best_appointment.appointment_wanted
            appointments_data.append(
                {
                    "id": best_appointment.id,
                    "doctor_name": appointment.doctor.name,
                    "especialidad": appointment.doctor.especialidad.name,
                    "location": appointment.doctor.especialidad.sucursal,
                    "tipo_de_turno": appointment.tipo_de_turno.name,
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

    def patch(self, request):
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

            # Check if the appointment belongs to the current user
            if best_appointment.patient.user != request.user:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Appointment does not belong to the current user",
                    },
                    status=401,
                )

            best_appointment.not_interested = not_interested
            best_appointment.save()

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

    def get(self, request):
        """Get all patients"""
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

    def post(self, request):
        """Create a new patient"""
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

    def delete(self, request):
        """Delete a patient"""
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

    def post(self, request):
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
            device.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Device registered successfully",
                "created": created,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ConfirmAppointmentView(LoginRequiredMixin, View):
    """Class-based view for confirming appointments"""

    def post(self, request):
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

        allende = Allende(auth_header=patient.token)

        appointment_data = {
            "CriterioBusquedaDto": {
                "IdPaciente": int(patient.id_paciente),
                "IdServicio": appointment.appointment_wanted.doctor.especialidad.id_servicio,
                "IdSucursal": appointment.appointment_wanted.doctor.especialidad.id_sucursal,
                "IdRecurso": appointment.appointment_wanted.doctor.id_recurso,
                "IdEspecialidad": appointment.appointment_wanted.doctor.especialidad.id_especialidad,
                "ControlarEdad": False,
                "IdTipoDeTurno": appointment.appointment_wanted.tipo_de_turno.id_tipo_prestacion,
                "IdFinanciador": int(patient.id_financiador),
                "IdTipoRecurso": appointment.appointment_wanted.doctor.id_tipo_recurso,
                "IdPlan": int(patient.id_plan),
                "Prestaciones": [
                    {
                        "IdPrestacion": appointment.appointment_wanted.tipo_de_turno.id_tipo_turno,
                        "IdItemSolicitudEstudios": 0,
                    }
                ],
            },
            "TurnoElegidoDto": {
                "Fecha": appointment.datetime.strftime("%Y-%m-%dT00:00:00"),
                "Hora": appointment.datetime.strftime("%H:%M"),
                "IdItemDePlantilla": appointment.id_item_plantilla,
                "IdPlantillaTurno": appointment.id_plantilla_turno,
                "IdSucursal": appointment.appointment_wanted.doctor.especialidad.id_sucursal,
                "DuracionIndividual": appointment.duracion_individual,
                "RequisitoAdministrativoAlOtorgar": "DNI\nCredencial Financiador\n AUTORIZACION: Con autorización online",
            },
            "Observaciones": None,
        }

        try:
            result = allende.reservar(appointment_data)
            id_turno = result.get("Entidad", {}).get("Id")
            if not id_turno:
                print(result)
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No se pudo obtener el ID del turno",
                    },
                    status=400,
                )

            appointment.confirmed_id_turno = id_turno
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
