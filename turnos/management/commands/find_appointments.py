from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from turnos.appointments import Allende
from turnos.models import BestAppointmentFound, FindAppointment, PacienteAllende
from turnos.selenium_utils import get_browser
from turnos.telegram import send_message


class Command(BaseCommand):
    help = "Find medical appointments"

    def login(self, user: PacienteAllende):
        driver = get_browser(settings.SELENIUM_HOSTNAME, settings.SELENIUM_PORT)
        driver.implicitly_wait(settings.SELENIUM_IMPLICIT_WAIT)

        allende = Allende(user.token)
        auth_header = allende.login(driver, user.docid, user.password)
        print(f"Updating token for {user.docid}")
        user.token = auth_header
        user.save()

        driver.close()
        driver.quit()

        return auth_header

    def handle(self, *args, **options):
        user = PacienteAllende.objects.first()
        if not Allende.is_authorized(user.token):
            self.login(user)
            # The token will get updated in the database
            user.refresh_from_db()

        allende = Allende(user.token)

        appointments_to_find = FindAppointment.objects.filter(active=True)
        for appointment in appointments_to_find:
            doctor_data = {
                "IdPaciente": user.id_paciente,
                "IdServicio": appointment.tipo_de_turno.id_servicio,
                "IdSucursal": appointment.doctor.id_sucursal,
                "IdRecurso": appointment.doctor.id_recurso,
                "IdEspecialidad": appointment.doctor.id_especialidad,
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
                print(
                    f"No new best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}"
                )
                continue

            if best_appointment_so_far is None:
                BestAppointmentFound.objects.create(
                    appointment_wanted=appointment,
                    datetime=new_best_appointment_datetime,
                )
                print(
                    f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}"
                )
                send_message(
                    f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}",
                    settings.TELEGRAM_TOKEN,
                    settings.TELEGRAM_CHAT_ID,
                )

            elif new_best_appointment_datetime == best_appointment_so_far.datetime:
                print("Appointment is the same")

            elif new_best_appointment_datetime < best_appointment_so_far.datetime:
                best_appointment_so_far.datetime = new_best_appointment_datetime
                best_appointment_so_far.save()
                print(
                    f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}"
                )
                send_message(
                    f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {new_best_appointment_datetime}",
                    settings.TELEGRAM_TOKEN,
                    settings.TELEGRAM_CHAT_ID,
                )

            else:
                print(
                    f"Lost best appointment for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {best_appointment_so_far.datetime}"
                )
                best_appointment_so_far.datetime = new_best_appointment_datetime
                best_appointment_so_far.save()
                send_message(
                    f"Lost best appointment for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: new date is {new_best_appointment_datetime}",
                    settings.TELEGRAM_TOKEN,
                    settings.TELEGRAM_CHAT_ID,
                )
