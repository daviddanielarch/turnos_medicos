import time
from typing import Any

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection

from sanatorio_allende.appointments import Allende
from sanatorio_allende.models import FindAppointment, PacienteAllende
from sanatorio_allende.services.appointment_handler import (
    AppointmentActionType,
    AppointmentHandler,
)
from sanatorio_allende.services.auth import AllendeAuthService


class Command(BaseCommand):
    help = "Find medical appointments"

    def check_database_connectivity(
        self, max_retries: int = 10, retry_delay: int = 2
    ) -> bool:
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

    def handle(self, *args: Any, **options: Any) -> None:
        if not self.check_database_connectivity():
            self.stdout.write(
                self.style.ERROR("Cannot proceed without database connectivity")
            )
            return

        self.stdout.write("Starting appointment search...")

        for patient in PacienteAllende.objects.all():
            assert isinstance(patient.id_paciente, str)
            assert isinstance(patient.user, User)

            auth_service = AllendeAuthService(patient)
            auth_service.login()

            allende = Allende(patient.token)
            appointments_to_find = FindAppointment.objects.filter(
                active=True, patient=patient
            )

            self.stdout.write(
                f"Found {appointments_to_find.count()} active appointments to check"
            )

            for appointment_to_find in appointments_to_find:
                self.stdout.write(
                    f"Checking appointments for {appointment_to_find.doctor_name} - {appointment_to_find.especialidad}"
                )

                doctor_data = {
                    "IdPaciente": int(patient.id_paciente),
                    "IdServicio": appointment_to_find.id_servicio,
                    "IdSucursal": appointment_to_find.id_sucursal,
                    "IdRecurso": appointment_to_find.id_recurso,
                    "IdEspecialidad": appointment_to_find.id_especialidad,
                    "IdTipoRecurso": appointment_to_find.id_tipo_recurso,
                    "ControlarEdad": False,
                    "IdFinanciador": patient.id_financiador,
                    "IdPlan": patient.id_plan,
                    "Prestaciones": [
                        {
                            "IdPrestacion": appointment_to_find.id_prestacion,
                            "IdItemSolicitudEstudios": 0,
                        }
                    ],
                }
                # Search for new appointment
                new_best_appointment_data = allende.search_best_date_appointment(
                    doctor_data
                )
                print(new_best_appointment_data)
                result = AppointmentHandler.process_appointment(
                    appointment_to_find=appointment_to_find,
                    patient=patient,
                    user=patient.user,
                    new_appointment_data=new_best_appointment_data,
                )

                # Log result
                if (
                    result.action == AppointmentActionType.CREATED
                    or result.action == AppointmentActionType.UPDATED
                ):
                    self.stdout.write(self.style.SUCCESS(result.message))
                elif result.action == AppointmentActionType.REMOVED:
                    self.stdout.write(self.style.WARNING(result.message))
                elif result.action == AppointmentActionType.SKIPPED:
                    self.stdout.write(self.style.WARNING(result.message))
                else:
                    self.stdout.write(result.message)

        self.stdout.write(
            self.style.SUCCESS("Appointment search completed successfully")
        )
