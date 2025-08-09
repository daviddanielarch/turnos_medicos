from typing import Any, Dict

from django.contrib.auth.models import User

from sanatorio_allende.services.appointment_processor import (
    AppointmentData,
    NotificationType,
)
from sanatorio_allende.services.push_notifications import PushNotificationService


class AppointmentNotificationService:
    """Service for handling appointment notifications"""

    @classmethod
    def send_appointment_notification(
        cls,
        appointment_data: AppointmentData,
        appointment_datetime: Any,  # datetime object
        notification_type: NotificationType,
        user: User,
    ) -> Dict[str, Any]:
        """
        Send push notification for appointment updates

        Args:
            appointment_data: Appointment information
            appointment_datetime: The appointment datetime
            message_type: Type of message ("new", "lost", etc.)
            user: The user to send notification to

        Returns:
            Dictionary with notification result
        """
        from sanatorio_allende.services.appointment_processor import (
            AppointmentProcessor,
        )

        # Format datetime for display
        datetime_str = AppointmentProcessor.format_appointment_datetime(
            appointment_datetime
        )

        # Create notification title
        if notification_type == NotificationType.NEW:
            push_title = (
                f"¡Nuevo turno! - {appointment_data.patient_dni} - "
                f"{appointment_data.doctor_name} - {datetime_str}"
            )
        else:
            push_title = (
                f"Turno perdido - {appointment_data.patient_dni} - "
                f"{appointment_data.doctor_name} - {datetime_str}"
            )

        # Create notification data
        notification_data = AppointmentProcessor.create_notification_data(
            appointment_data, appointment_datetime, notification_type
        )

        # Send push notification
        push_result = PushNotificationService.send_notification(
            title=push_title,
            body=f"{appointment_data.doctor_name} - {appointment_data.especialidad_name} "
            f"({appointment_data.tipo_de_turno_name})",
            data={"type": "appointment_update", "appointment": notification_data},
            sound="default",
            priority="high",
            user=user,
        )

        return push_result

    @classmethod
    def log_notification_result(
        cls,
        push_result: Dict[str, Any],
        appointment_data: AppointmentData,
        notification_type: NotificationType,
    ) -> None:
        """
        Log notification results (for use in command output)

        Args:
            push_result: Result from push notification service
            appointment_data: Appointment information
            notification_type: Type of notification sent
        """
        if push_result["success"]:
            print(
                f"Push notification sent to {push_result['sent_count']}/"
                f"{push_result['total_devices']} devices for {appointment_data.doctor_name}"
            )

            # Log receipt IDs if available
            if push_result.get("receipt_ids"):
                print(f"Receipt IDs generated: {len(push_result['receipt_ids'])}")

            # Log any errors that occurred
            if push_result.get("errors"):
                print(
                    f"Some push notification errors: {len(push_result['errors'])} errors"
                )
                for error in push_result["errors"]:
                    print(f"  - {error}")
        else:
            print(
                f"Push notification failed: {push_result.get('error', 'Unknown error')} "
                f"for {appointment_data.doctor_name}"
            )
