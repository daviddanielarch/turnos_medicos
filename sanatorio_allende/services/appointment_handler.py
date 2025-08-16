from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from django.contrib.auth.models import User

from sanatorio_allende.models import (
    BestAppointmentFound,
    FindAppointment,
    PacienteAllende,
)
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


class AppointmentActionType(Enum):
    """Types of actions that can be performed on appointments"""

    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    SKIPPED = "skipped"
    NONE = "none"


@dataclass
class AppointmentProcessingResult:
    """Result of appointment processing operation"""

    action: AppointmentActionType
    message: str
    notification_sent: bool = False


class AppointmentHandler:
    """Simplified service to handle all appointment processing logic"""

    @classmethod
    def process_appointment(
        cls,
        appointment_to_find: FindAppointment,
        patient: PacienteAllende,
        user: User,
        new_appointment_data: Optional[dict] = None,
    ) -> AppointmentProcessingResult:
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
        new_appointment_data = new_appointment_data or {"datetime": None}
        new_appointment_datetime = new_appointment_data["datetime"]

        # Get current best appointment
        best_appointment_so_far = (
            BestAppointmentRepository.get_current_best_appointment(
                appointment_to_find, patient
            )
        )

        # Prepare comparison data
        current_best_datetime = (
            best_appointment_so_far.datetime if best_appointment_so_far else None
        )

        # Get all not_interested appointments
        not_interested_appointments = (
            BestAppointmentRepository.get_not_interested_appointments(
                appointment_to_find, patient
            )
        )
        not_interested_datetimes = [
            appt.datetime for appt in not_interested_appointments
        ]

        # Check timeframe only for new appointments (not for better appointments)
        if current_best_datetime is None:
            if new_appointment_datetime is None:
                return AppointmentProcessingResult(
                    action=AppointmentActionType.SKIPPED,
                    message="No new appointment found",
                    notification_sent=False,
                )

            # For new appointments, check if within desired timeframe
            if (
                appointment_to_find.desired_timeframe is not None
                and not AppointmentProcessor.is_within_desired_timeframe(
                    new_appointment_datetime, appointment_to_find.desired_timeframe
                )
            ):
                return AppointmentProcessingResult(
                    action=AppointmentActionType.SKIPPED,
                    message=f"Appointment {new_appointment_datetime} is outside desired timeframe ({appointment_to_find.desired_timeframe}) for {appointment_to_find.doctor.name} - {appointment_to_find.tipo_de_turno.name}",
                    notification_sent=False,
                )

        # Compare appointments
        comparison_result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime, current_best_datetime, not_interested_datetimes
        )

        # Create appointment data for notifications and processing
        complete_appointment_data = AppointmentData(
            doctor_name=appointment_to_find.doctor.name,
            especialidad_name=appointment_to_find.doctor.especialidad.name,
            tipo_de_turno_name=appointment_to_find.tipo_de_turno.name,
            patient_dni=patient.docid,
            desired_timeframe=appointment_to_find.desired_timeframe
            or FindAppointment.DEFAULT_DESIRED_TIMEFRAME,
            duracion_individual=new_appointment_data.get("duracion_individual"),
            id_plantilla_turno=new_appointment_data.get("id_plantilla_turno"),
            id_item_plantilla=new_appointment_data.get("id_item_plantilla"),
        )

        result = cls._handle_action(
            comparison_result,
            appointment_to_find,
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
    ) -> AppointmentProcessingResult:
        """Handle the specific action from comparison result"""

        if comparison_result.action == AppointmentAction.CREATE_NEW:
            assert isinstance(comparison_result.new_datetime, datetime)

            BestAppointmentRepository.create_best_appointment(
                appointment,
                patient,
                comparison_result.new_datetime,
                duracion_individual=appointment_data.duracion_individual,
                id_plantilla_turno=appointment_data.id_plantilla_turno,
                id_item_plantilla=appointment_data.id_item_plantilla,
            )

            result = AppointmentProcessingResult(
                action=AppointmentActionType.CREATED,
                message=f"New best appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {comparison_result.new_datetime}",
            )

        elif comparison_result.action == AppointmentAction.UPDATE_EXISTING:
            assert isinstance(comparison_result.new_datetime, datetime)
            best_appointment_so_far = (
                BestAppointmentRepository.get_current_best_appointment(
                    appointment, patient
                )
            )
            assert isinstance(best_appointment_so_far, BestAppointmentFound)

            BestAppointmentRepository.update_best_appointment(
                best_appointment_so_far,
                comparison_result.new_datetime,
                duracion_individual=appointment_data.duracion_individual,
                id_plantilla_turno=appointment_data.id_plantilla_turno,
                id_item_plantilla=appointment_data.id_item_plantilla,
            )

            result = AppointmentProcessingResult(
                action=AppointmentActionType.UPDATED,
                message=f"Better appointment found for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {comparison_result.new_datetime}",
            )

        elif comparison_result.action == AppointmentAction.REMOVE_EXISTING:
            best_appointment_so_far = (
                BestAppointmentRepository.get_current_best_appointment(
                    appointment, patient
                )
            )
            assert isinstance(best_appointment_so_far, BestAppointmentFound)
            BestAppointmentRepository.delete_previous_appointments(
                best_appointment_so_far
            )

            result = AppointmentProcessingResult(
                action=AppointmentActionType.REMOVED,
                message=f"Removed worse appointments for {appointment.doctor.name} - {appointment.tipo_de_turno.name}: {comparison_result.previous_datetime}",
            )

        else:  # DO_NOTHING
            result = AppointmentProcessingResult(
                action=AppointmentActionType.SKIPPED,
                message="No action needed",
            )

        # Send notification if needed
        if comparison_result.should_notify:
            notification_datetime = (
                comparison_result.previous_datetime
                if comparison_result.action == AppointmentAction.REMOVE_EXISTING
                else comparison_result.new_datetime
            )
            push_result = AppointmentNotificationService.send_appointment_notification(
                appointment_data,
                notification_datetime,
                comparison_result.notification_type,
                user,
            )
            AppointmentNotificationService.log_notification_result(
                push_result, appointment_data, comparison_result.notification_type
            )
            result.notification_sent = True
        else:
            result.notification_sent = False

        return result
