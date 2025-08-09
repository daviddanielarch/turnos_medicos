import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class AppointmentAction(Enum):
    """Actions to take based on appointment comparison"""

    CREATE_NEW = "create_new"
    UPDATE_EXISTING = "update_existing"
    REMOVE_EXISTING = "remove_existing"
    DO_NOTHING = "do_nothing"


class NotificationType(Enum):
    """Types of notifications for appointment updates"""

    NEW = "new"
    LOST = "lost"
    NONE = "none"


@dataclass
class AppointmentData:
    """Data structure for appointment information without Django dependencies"""

    doctor_name: str
    especialidad_name: str
    tipo_de_turno_name: str
    patient_dni: str
    desired_timeframe: str


@dataclass
class AppointmentComparisonResult:
    """Result of comparing current and new appointment datetimes"""

    action: AppointmentAction
    new_datetime: datetime.datetime
    previous_datetime: Optional[datetime.datetime]
    should_notify: bool
    notification_type: NotificationType


class AppointmentProcessor:
    """Service for processing appointment logic with datetime objects"""

    TIMEFRAME_BOUNDARIES = {
        "1 week": datetime.timedelta(days=7),
        "2 weeks": datetime.timedelta(days=14),
        "3 weeks": datetime.timedelta(days=21),
        "anytime": datetime.timedelta(days=365),
    }

    @classmethod
    def is_within_desired_timeframe(
        cls,
        appointment_datetime: datetime.datetime,
        desired_timeframe: str,
        current_time: Optional[datetime.datetime] = None,
    ) -> bool:
        """
        Check if appointment datetime is within the desired timeframe

        Args:
            appointment_datetime: The appointment datetime to check
            desired_timeframe: The desired timeframe string
            current_time: Current time (defaults to now if None)

        Returns:
            True if appointment is within desired timeframe, False otherwise
        """
        if current_time is None:
            current_time = datetime.datetime.now()

        if appointment_datetime.tzinfo is None:
            # Make naive datetime timezone-aware
            from django.utils import timezone

            appointment_datetime = timezone.make_aware(appointment_datetime)

        if current_time.tzinfo is None:
            # Make naive datetime timezone-aware
            from django.utils import timezone

            current_time = timezone.make_aware(current_time)

        boundary = cls.TIMEFRAME_BOUNDARIES.get(desired_timeframe)
        if boundary is None:
            raise ValueError(f"Invalid desired_timeframe: {desired_timeframe}")

        return appointment_datetime <= current_time + boundary

    @classmethod
    def compare_appointments(
        cls,
        new_appointment_datetime: datetime.datetime,
        current_best_datetime: Optional[datetime.datetime],
        not_interested_datetimes: list[datetime.datetime] = None,
    ) -> AppointmentComparisonResult:
        """
        Compare new appointment datetime with current best appointment and not_interested appointments

        Args:
            new_appointment_datetime: The newly found appointment datetime
            current_best_datetime: The current best appointment datetime (None if no previous)
            not_interested_datetimes: List of not_interested appointment datetimes

        Returns:
            AppointmentComparisonResult with comparison details
        """
        if not_interested_datetimes is None:
            not_interested_datetimes = []

        # Ensure timezone awareness
        if new_appointment_datetime.tzinfo is None:
            from django.utils import timezone

            new_appointment_datetime = timezone.make_aware(new_appointment_datetime)

        if current_best_datetime and current_best_datetime.tzinfo is None:
            from django.utils import timezone

            current_best_datetime = timezone.make_aware(current_best_datetime)

        # Make all not_interested datetimes timezone-aware
        not_interested_datetimes = [
            timezone.make_aware(dt) if dt.tzinfo is None else dt
            for dt in not_interested_datetimes
        ]

        # Check if new appointment matches any not_interested appointment
        if new_appointment_datetime in not_interested_datetimes:
            return AppointmentComparisonResult(
                action=AppointmentAction.DO_NOTHING,
                new_datetime=new_appointment_datetime,
                previous_datetime=new_appointment_datetime,
                should_notify=False,
                notification_type=NotificationType.NONE,
            )

        # No previous appointment found
        if current_best_datetime is None:
            return AppointmentComparisonResult(
                action=AppointmentAction.CREATE_NEW,
                new_datetime=new_appointment_datetime,
                previous_datetime=None,
                should_notify=True,
                notification_type=NotificationType.NEW,
            )

        # Same appointment
        if new_appointment_datetime == current_best_datetime:
            return AppointmentComparisonResult(
                action=AppointmentAction.DO_NOTHING,
                new_datetime=new_appointment_datetime,
                previous_datetime=current_best_datetime,
                should_notify=False,
                notification_type=NotificationType.NONE,
            )

        # New appointment is later than current (worse appointment)
        if new_appointment_datetime > current_best_datetime:
            return AppointmentComparisonResult(
                action=AppointmentAction.REMOVE_EXISTING,
                new_datetime=new_appointment_datetime,
                previous_datetime=current_best_datetime,
                should_notify=True,
                notification_type=NotificationType.LOST,
            )

        # New appointment is earlier than current (better appointment)
        return AppointmentComparisonResult(
            action=AppointmentAction.UPDATE_EXISTING,
            new_datetime=new_appointment_datetime,
            previous_datetime=current_best_datetime,
            should_notify=True,
            notification_type=NotificationType.NEW,
        )

    @classmethod
    def create_appointment_data(
        cls,
        doctor_name: str,
        especialidad_name: str,
        tipo_de_turno_name: str,
        patient_dni: str,
        desired_timeframe: str,
    ) -> AppointmentData:
        """
        Create AppointmentData object from individual fields

        Args:
            doctor_name: Name of the doctor
            especialidad_name: Name of the specialty
            tipo_de_turno_name: Name of the appointment type
            patient_dni: Patient's DNI
            desired_timeframe: Desired timeframe for the appointment

        Returns:
            AppointmentData object
        """
        return AppointmentData(
            doctor_name=doctor_name,
            especialidad_name=especialidad_name,
            tipo_de_turno_name=tipo_de_turno_name,
            patient_dni=patient_dni,
            desired_timeframe=desired_timeframe,
        )

    @classmethod
    def format_appointment_datetime(
        cls, appointment_datetime: datetime.datetime
    ) -> str:
        """
        Format appointment datetime for display

        Args:
            appointment_datetime: The datetime to format

        Returns:
            Formatted datetime string
        """
        return appointment_datetime.strftime("%d/%m/%Y %H:%M")

    @classmethod
    def create_notification_data(
        cls,
        appointment_data: AppointmentData,
        appointment_datetime: datetime.datetime,
        notification_type: NotificationType,
    ) -> Dict[str, Any]:
        """
        Create notification data for push notifications

        Args:
            appointment_data: Appointment information
            appointment_datetime: The appointment datetime
            notification_type: Type of notification (NEW, LOST, etc.)

        Returns:
            Dictionary with notification data
        """
        return {
            "name": appointment_data.doctor_name,
            "especialidad": appointment_data.especialidad_name,
            "tipo_de_turno": appointment_data.tipo_de_turno_name,
            "datetime": cls.format_appointment_datetime(appointment_datetime),
            "message_type": notification_type.value,
        }
