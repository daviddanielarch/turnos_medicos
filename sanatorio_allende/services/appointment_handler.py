from typing import Optional

from django.contrib.auth.models import User

from sanatorio_allende.models import FindAppointment, PacienteAllende
from sanatorio_allende.repositories.best_appointment_repository import (
    BestAppointmentRepository,
)
from sanatorio_allende.services.appointment_notification_service import (
    AppointmentNotificationService,
)
from sanatorio_allende.services.appointment_processor import (
    AppointmentAction,
    AppointmentComparisonResult,
    AppointmentData,
    AppointmentProcessor,
)


class AppointmentHandler:
    """Simplified service to handle all appointment processing logic"""

    @classmethod
    def process_appointment(
        cls,
        appointment: FindAppointment,
        patient: PacienteAllende,
        user: User,
        appointment_data: Optional[dict] = None,
    ) -> dict:
        """
        Process a new appointment and handle all logic in one place

        Args:
            appointment: The FindAppointment object
            patient: The PacienteAllende object
            appointment_data: Dictionary containing appointment data including datetime and additional fields
            user: The user to send notifications to

        Returns:
            Dictionary with processing result
        """
        new_appointment_datetime = (
            appointment_data["datetime"] if appointment_data else None
        )

        # Get current best appointment
        best_appointment_so_far = (
            BestAppointmentRepository.get_current_best_appointment(appointment, patient)
        )

        # Prepare comparison data
        current_best_datetime = (
            best_appointment_so_far.datetime if best_appointment_so_far else None
        )

        # Get all not_interested appointments
        not_interested_appointments = (
            BestAppointmentRepository.get_not_interested_appointments(
                appointment, patient
            )
        )
        not_interested_datetimes = [
            appt.datetime for appt in not_interested_appointments
        ]

        # Check timeframe only for new appointments (not for better appointments)
        if current_best_datetime is None:
            # For new appointments, check if within desired timeframe
            if not AppointmentProcessor.is_within_desired_timeframe(
                new_appointment_datetime, appointment.desired_timeframe
            ):
                return {
                    "action": "skipped",
                    "message": f"Appointment {new_appointment_datetime} is outside desired timeframe ({appointment.desired_timeframe}) for {appointment.doctor.name} - {appointment.tipo_de_turno.name}",
                    "success": False,
                    "notification_sent": False,
                }

        # Compare appointments
        comparison_result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime, current_best_datetime, not_interested_datetimes
        )

        # Create appointment data for notifications and processing
        complete_appointment_data = AppointmentProcessor.create_appointment_data(
            doctor_name=appointment.doctor.name,
            especialidad_name=appointment.doctor.especialidad.name,
            tipo_de_turno_name=appointment.tipo_de_turno.name,
            patient_dni=patient.docid,
            desired_timeframe=appointment.desired_timeframe,
            duracion_individual=appointment_data.get("duracion_individual"),
            id_plantilla_turno=appointment_data.get("id_plantilla_turno"),
            id_item_plantilla=appointment_data.get("id_item_plantilla"),
            hora=appointment_data.get("hora"),
        )

        # Handle the action
        result = cls._handle_action(
            comparison_result,
            appointment,
            patient,
            complete_appointment_data,
            user,
        )

        return result

    @classmethod
    def _handle_action(
        cls,
        comparison_result: AppointmentComparisonResult,
        appointment: FindAppointment,
        patient: PacienteAllende,
        appointment_data: AppointmentData,
        user: User,
    ) -> dict:
        """Handle the specific action from comparison result"""

        if comparison_result.action == AppointmentAction.CREATE_NEW:
            # Create new best appointment
            BestAppointmentRepository.create_best_appointment(
                appointment,
                patient,
                comparison_result.new_datetime,
                duracion_individual=appointment_data.duracion_individual,
                id_plantilla_turno=appointment_data.id_plantilla_turno,
                id_item_plantilla=appointment_data.id_item_plantilla,
                hora=appointment_data.hora,
            )

            result = {
                "action": "created",
                "message": f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {comparison_result.new_datetime}",
                "success": True,
            }

        elif comparison_result.action == AppointmentAction.UPDATE_EXISTING:
            # Update existing best appointment
            best_appointment_so_far = (
                BestAppointmentRepository.get_current_best_appointment(
                    appointment, patient
                )
            )
            BestAppointmentRepository.update_best_appointment(
                best_appointment_so_far,
                comparison_result.new_datetime,
                duracion_individual=appointment_data.duracion_individual,
                id_plantilla_turno=appointment_data.id_plantilla_turno,
                id_item_plantilla=appointment_data.id_item_plantilla,
                hora=appointment_data.hora,
            )

            result = {
                "action": "updated",
                "message": f"Better appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {comparison_result.new_datetime}",
                "success": True,
            }

        elif comparison_result.action == AppointmentAction.REMOVE_EXISTING:
            # Remove existing appointment
            best_appointment_so_far = (
                BestAppointmentRepository.get_current_best_appointment(
                    appointment, patient
                )
            )
            BestAppointmentRepository.delete_previous_appointments(
                best_appointment_so_far
            )

            result = {
                "action": "removed",
                "message": f"Removed worse appointments for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {comparison_result.previous_datetime}",
                "success": True,
            }

        else:  # DO_NOTHING
            result = {
                "action": "none",
                "message": "No action needed",
                "success": True,
            }

        # Send notification if needed
        if comparison_result.should_notify:
            datetime = (
                comparison_result.previous_datetime
                if comparison_result.action == AppointmentAction.REMOVE_EXISTING
                else comparison_result.new_datetime
            )
            push_result = AppointmentNotificationService.send_appointment_notification(
                appointment_data,
                datetime,
                comparison_result.notification_type,
                user,
            )
            AppointmentNotificationService.log_notification_result(
                push_result, appointment_data, comparison_result.notification_type
            )
            result["notification_sent"] = True
        else:
            result["notification_sent"] = False

        return result
