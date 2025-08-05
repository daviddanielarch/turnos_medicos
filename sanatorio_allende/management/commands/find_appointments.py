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
from sanatorio_allende.services.push_notifications import PushNotificationService


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

    def send_notifications(
        self, appointment, new_best_appointment_datetime, message_type="new"
    ):
        """
        Send push notifications to Android devices
        """
        doctor_name = appointment.doctor.name
        especialidad = appointment.doctor.especialidad.name
        tipo_de_turno = appointment.tipo_de_turno.name
        datetime_str = new_best_appointment_datetime.strftime("%d/%m/%Y %H:%M")
        patient_dni = appointment.patient.docid

        if message_type == "new":
            push_title = (
                f"¡Nuevo turno! - {patient_dni} - {doctor_name} - {datetime_str}"
            )
        else:
            push_title = (
                f"Turno perdido - {patient_dni} - {doctor_name} - {datetime_str}"
            )

        try:
            appointment_data = {
                "name": doctor_name,
                "especialidad": especialidad,
                "tipo_de_turno": tipo_de_turno,
                "datetime": datetime_str,
                "message_type": message_type,
            }

            self.stdout.write(f"Sending push notification: {push_title}")

            # Use the generic send_notification method to customize title
            push_result = PushNotificationService.send_notification(
                title=push_title,
                body=f"{doctor_name} - {especialidad} ({tipo_de_turno})",
                data={"type": "appointment_update", "appointment": appointment_data},
                sound="default",
                priority="high",
                user=appointment.patient.user,
            )

            if push_result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Push notification sent to {push_result['sent_count']}/{push_result['total_devices']} devices"
                    )
                )

                # Log receipt IDs if available
                if push_result.get("receipt_ids"):
                    self.stdout.write(
                        f"Receipt IDs generated: {len(push_result['receipt_ids'])}"
                    )

                # Log any errors that occurred
                if push_result.get("errors"):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Some push notification errors: {len(push_result['errors'])} errors"
                        )
                    )
                    for error in push_result["errors"]:
                        self.stdout.write(f"  - {error}")
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Push notification failed: {push_result.get('error', 'Unknown error')}"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send push notification: {str(e)}")
            )

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
                    "Prestaciones": [
                        {
                            "IdPrestacion": appointment.tipo_de_turno.id_tipo_turno,
                            "IdItemSolicitudEstudios": 0,
                        }
                    ],
                }
                print(doctor_data)
                try:
                    best_appointment_so_far = BestAppointmentFound.objects.get(
                        appointment_wanted=appointment, patient=patient
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
                        patient=patient,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}"
                        )
                    )
                    self.send_notifications(
                        appointment, new_best_appointment_datetime, "new"
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
                    self.send_notifications(
                        appointment, new_best_appointment_datetime, "new"
                    )

                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Lost best appointment for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {best_appointment_so_far.datetime}"
                        )
                    )
                    best_appointment_so_far.datetime = new_best_appointment_datetime
                    best_appointment_so_far.save()
                    self.send_notifications(
                        appointment, new_best_appointment_datetime, "lost"
                    )

        self.stdout.write(
            self.style.SUCCESS("Appointment search completed successfully")
        )
