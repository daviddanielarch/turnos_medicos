import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import AppointmentType, BestAppointmentFound, Doctor, FindAppointment


@csrf_exempt
@require_http_methods(["GET"])
def api_doctors(request):
    """API endpoint to get all doctors with their specialties and locations"""
    try:
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
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_appointment_types(request):
    """API endpoint to get appointment types for a specific doctor"""
    try:
        doctor_id = request.GET.get("doctor_id")
        if not doctor_id:
            return JsonResponse(
                {"success": False, "error": "doctor_id parameter is required"},
                status=400,
            )

        doctor = Doctor.objects.get(id=doctor_id)
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
    except Doctor.DoesNotExist:
        return JsonResponse({"success": False, "error": "Doctor not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_appointment(request):
    """API endpoint to create a new FindAppointment"""
    try:
        data = json.loads(request.body)
        doctor_id = data.get("doctor_id")
        appointment_type_id = data.get("appointment_type_id")

        if not doctor_id or not appointment_type_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "doctor_id and appointment_type_id are required",
                },
                status=400,
            )

        doctor = Doctor.objects.get(id=doctor_id)
        appointment_type = AppointmentType.objects.get(id=appointment_type_id)

        # Check if appointment already exists
        existing_appointment = FindAppointment.objects.filter(
            doctor=doctor, tipo_de_turno=appointment_type
        ).first()

        if existing_appointment:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Appointment already exists for this doctor and service type",
                },
                status=400,
            )

        # Create new appointment
        appointment = FindAppointment.objects.create(
            doctor=doctor,
            tipo_de_turno=appointment_type,
            active=True,  # Default to active
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Appointment created successfully",
                "appointment_id": appointment.id,
            }
        )
    except Doctor.DoesNotExist:
        return JsonResponse({"success": False, "error": "Doctor not found"}, status=404)
    except AppointmentType.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Appointment type not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_find_appointments(request):
    """API endpoint to get all FindAppointment objects"""
    try:
        find_appointments = FindAppointment.objects.select_related(
            "doctor",
            "doctor__especialidad",
            "tipo_de_turno",
        ).all()

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
                }
            )

        return JsonResponse({"success": True, "appointments": appointments_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_appointment_status(request):
    """API endpoint to update the active status of a FindAppointment"""
    try:
        data = json.loads(request.body)
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

        appointment = FindAppointment.objects.get(id=appointment_id)
        appointment.active = active
        appointment.save()

        return JsonResponse(
            {
                "success": True,
                "message": f'Appointment status updated to {"active" if active else "inactive"}',
            }
        )
    except FindAppointment.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Appointment not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_best_appointments(request):
    """API endpoint to get all BestAppointmentFound objects"""
    try:
        best_appointments = BestAppointmentFound.objects.select_related(
            "appointment_wanted",
            "appointment_wanted__doctor",
            "appointment_wanted__doctor__especialidad",
            "appointment_wanted__tipo_de_turno",
        ).all()

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
                    "formatted_datetime": best_appointment.datetime.strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    "doctor_id": appointment.doctor.id,
                    "tipo_de_turno_id": appointment.tipo_de_turno.id,
                    "appointment_wanted_id": appointment.id,
                }
            )

        return JsonResponse({"success": True, "best_appointments": appointments_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
