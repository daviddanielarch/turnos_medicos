import datetime
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from sanatorio_allende.appointments import Allende
from sanatorio_allende.models import (
    BestAppointmentFound,
    FindAppointment,
    PacienteAllende,
)
from sanatorio_allende.services.appointment_handler import AppointmentHandler
from sanatorio_allende.services.appointment_processor import AppointmentProcessor
from sanatorio_allende.services.auth import AllendeAuthService


class Command(BaseCommand):
    help = "Find medical appointments"

    def check_database_connectivity(self, max_retries=10, retry_delay=2):
        """
        Check if the database is accessible, since the database needs to wake up.
        """
        self.stdout.write("Checking database connectivity...")

        for attempt in range(max_retries):
            try:
                with connection.cursor() as cursor:
                    # Simple query to wake up the database
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Database connection successful (attempt {attempt + 1})"
                    )
                )
                return True

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Database connection attempt {attempt + 1} failed: {str(e)}"
                    )
                )

                if attempt < max_retries - 1:
                    self.stdout.write(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Increase delay for subsequent attempts
                    retry_delay *= 2
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            "Failed to connect to database after all retries"
                        )
                    )
                    return False

        return False

    def handle(self, *args, **options):
        if not self.check_database_connectivity():
            self.stdout.write(
                self.style.ERROR("Cannot proceed without database connectivity")
            )
            return

        self.stdout.write("Starting appointment search...")

        for patient in PacienteAllende.objects.all():
            auth_service = AllendeAuthService(patient)
            auth_service.login()

            allende = Allende(patient.token)
            appointments_to_find = FindAppointment.objects.filter(
                active=True, patient=patient
            )

            self.stdout.write(
                f"Found {appointments_to_find.count()} active appointments to check"
            )

            for appointment in appointments_to_find:
                self.stdout.write(
                    f"Checking appointments for {appointment.doctor.name} - {appointment.tipo_de_turno.name}"
                )

                doctor_data = {
                    "IdPaciente": int(patient.id_paciente),
                    "IdServicio": appointment.doctor.especialidad.id_servicio,
                    "IdSucursal": appointment.doctor.especialidad.id_sucursal,
                    "IdRecurso": appointment.doctor.id_recurso,
                    "IdEspecialidad": appointment.doctor.especialidad.id_especialidad,
                    "IdTipoRecurso": appointment.doctor.id_tipo_recurso,
                    "ControlarEdad": False,
                    "IdFinanciador": patient.id_financiador,
                    "IdPlan": patient.id_plan,
                    "Prestaciones": [
                        {
                            "IdPrestacion": appointment.tipo_de_turno.id_tipo_turno,
                            "IdItemSolicitudEstudios": 0,
                        }
                    ],
                }

                # Search for new appointment
                new_best_appointment_data = allende.search_best_date_appointment(
                    doctor_data
                )

                # Process appointment using simplified handler
                result = AppointmentHandler.process_appointment(
                    appointment=appointment,
                    patient=patient,
                    user=patient.user,
                    appointment_data=new_best_appointment_data,
                )

                # Log result
                if result["action"] == "created" or result["action"] == "updated":
                    self.stdout.write(self.style.SUCCESS(result["message"]))
                elif result["action"] == "removed":
                    self.stdout.write(self.style.WARNING(result["message"]))
                elif result["action"] == "skipped":
                    self.stdout.write(self.style.WARNING(result["message"]))
                else:
                    self.stdout.write(result["message"])

        self.stdout.write(
            self.style.SUCCESS("Appointment search completed successfully")
        )
