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
from sanatorio_allende.services.auth import AllendeAuthService
from sanatorio_allende.telegram import send_message


class Command(BaseCommand):
    help = "Find medical appointments"

    def check_database_connectivity(self, max_retries=3, retry_delay=2):
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
        # Check database connectivity first
        if not self.check_database_connectivity():
            self.stdout.write(
                self.style.ERROR("Cannot proceed without database connectivity")
            )
            return

        self.stdout.write("Starting appointment search...")

        user = PacienteAllende.objects.first()
        auth_service = AllendeAuthService(user)
        auth_service.login()

        allende = Allende(user.token)
        appointments_to_find = FindAppointment.objects.filter(active=True)

        self.stdout.write(
            f"Found {appointments_to_find.count()} active appointments to check"
        )

        for appointment in appointments_to_find:
            self.stdout.write(
                f"Checking appointments for {appointment.doctor.name} - {appointment.tipo_de_turno.name}"
            )

            doctor_data = {
                "IdPaciente": user.id_paciente,
                "IdServicio": appointment.doctor.especialidad.id_servicio,
                "IdSucursal": appointment.doctor.especialidad.id_sucursal,
                "IdRecurso": appointment.doctor.id_recurso,
                "IdEspecialidad": appointment.doctor.especialidad.id_especialidad,
                "IdTipoRecurso": appointment.doctor.id_tipo_recurso,
                "Prestaciones": [
                    {
                        "IdPrestacion": appointment.tipo_de_turno.id_tipo_turno,
                        "IdItemSolicitudEstudios": 0,
                    }
                ],
            }

            try:
                best_appointment_so_far = BestAppointmentFound.objects.get(
                    appointment_wanted=appointment
                )
            except BestAppointmentFound.DoesNotExist:
                best_appointment_so_far = None

            new_best_appointment_datetime = allende.search_best_date_appointment(
                doctor_data
            )

            # Make the naive datetime timezone-aware
            if new_best_appointment_datetime:
                new_best_appointment_datetime = timezone.make_aware(
                    new_best_appointment_datetime
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"No new best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}"
                    )
                )
                continue

            if best_appointment_so_far is None:
                BestAppointmentFound.objects.create(
                    appointment_wanted=appointment,
                    datetime=new_best_appointment_datetime,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}"
                    )
                )
                send_message(
                    f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}",
                    settings.TELEGRAM_TOKEN,
                    settings.TELEGRAM_CHAT_ID,
                )

            elif new_best_appointment_datetime == best_appointment_so_far.datetime:
                self.stdout.write("Appointment is the same")

            elif new_best_appointment_datetime < best_appointment_so_far.datetime:
                best_appointment_so_far.datetime = new_best_appointment_datetime
                best_appointment_so_far.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}"
                    )
                )
                send_message(
                    f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}",
                    settings.TELEGRAM_TOKEN,
                    settings.TELEGRAM_CHAT_ID,
                )

            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Lost best appointment for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {best_appointment_so_far.datetime}"
                    )
                )
                best_appointment_so_far.datetime = new_best_appointment_datetime
                best_appointment_so_far.save()
                send_message(
                    f"Lost best appointment for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: new date is {new_best_appointment_datetime}",
                    settings.TELEGRAM_TOKEN,
                    settings.TELEGRAM_CHAT_ID,
                )

        self.stdout.write(
            self.style.SUCCESS("Appointment search completed successfully")
        )
