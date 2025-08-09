from typing import Optional

from django.utils import timezone

from sanatorio_allende.models import (
    BestAppointmentFound,
    FindAppointment,
    PacienteAllende,
)


class BestAppointmentRepository:
    """Service for handling BestAppointmentFound database operations"""

    @classmethod
    def get_current_best_appointment(
        cls, appointment_wanted: FindAppointment, patient: PacienteAllende
    ) -> Optional[BestAppointmentFound]:
        """
        Get the current best appointment (not marked as not_interested) for a specific appointment wanted and patient

        Args:
            appointment_wanted: The FindAppointment object
            patient: The PacienteAllende object

        Returns:
            BestAppointmentFound object if exists, None otherwise
        """
        try:
            return BestAppointmentFound.objects.get(
                appointment_wanted=appointment_wanted,
                patient=patient,
                not_interested=False,
            )
        except BestAppointmentFound.DoesNotExist:
            return None

    @classmethod
    def get_all_appointments(
        cls, appointment_wanted: FindAppointment, patient: PacienteAllende
    ) -> list[BestAppointmentFound]:
        """
        Get all appointments for a specific appointment wanted and patient

        Args:
            appointment_wanted: The FindAppointment object
            patient: The PacienteAllende object

        Returns:
            List of BestAppointmentFound objects
        """
        return list(
            BestAppointmentFound.objects.filter(
                appointment_wanted=appointment_wanted, patient=patient
            ).order_by("datetime")
        )

    @classmethod
    def get_not_interested_appointments(
        cls, appointment_wanted: FindAppointment, patient: PacienteAllende
    ) -> list[BestAppointmentFound]:
        """
        Get all not_interested appointments for a specific appointment wanted and patient

        Args:
            appointment_wanted: The FindAppointment object
            patient: The PacienteAllende object

        Returns:
            List of BestAppointmentFound objects with not_interested=True
        """
        return list(
            BestAppointmentFound.objects.filter(
                appointment_wanted=appointment_wanted,
                patient=patient,
                not_interested=True,
            ).order_by("datetime")
        )

    @classmethod
    def create_best_appointment(
        cls,
        appointment_wanted: FindAppointment,
        patient: PacienteAllende,
        appointment_datetime: timezone.datetime,
        not_interested: bool = False,
    ) -> BestAppointmentFound:
        """
        Create a new BestAppointmentFound record

        Args:
            appointment_wanted: The FindAppointment object
            patient: The PacienteAllende object
            appointment_datetime: The appointment datetime
            not_interested: Whether the patient is not interested in this appointment

        Returns:
            Created BestAppointmentFound object
        """
        return BestAppointmentFound.objects.create(
            appointment_wanted=appointment_wanted,
            datetime=appointment_datetime,
            patient=patient,
            not_interested=not_interested,
        )

    @classmethod
    def update_best_appointment(
        cls, best_appointment: BestAppointmentFound, new_datetime: timezone.datetime
    ) -> BestAppointmentFound:
        """
        Update an existing BestAppointmentFound record with new datetime

        Args:
            best_appointment: The BestAppointmentFound object to update
            new_datetime: The new appointment datetime

        Returns:
            Updated BestAppointmentFound object
        """
        best_appointment.datetime = new_datetime
        best_appointment.save()
        return best_appointment

    @classmethod
    def delete_previous_appointments(
        cls, best_appointment: BestAppointmentFound
    ) -> None:
        """
        Delete a BestAppointmentFound record

        Args:
            best_appointment: The BestAppointmentFound object to delete
        """
        BestAppointmentFound.objects.filter(
            appointment_wanted=best_appointment.appointment_wanted,
            patient=best_appointment.patient,
            datetime__lte=best_appointment.datetime,
        ).delete()

    @classmethod
    def get_or_create_best_appointment(
        cls,
        appointment_wanted: FindAppointment,
        patient: PacienteAllende,
        appointment_datetime: timezone.datetime,
    ) -> tuple[BestAppointmentFound, bool]:
        """
        Get existing BestAppointmentFound or create new one

        Args:
            appointment_wanted: The FindAppointment object
            patient: The PacienteAllende object
            appointment_datetime: The appointment datetime

        Returns:
            Tuple of (BestAppointmentFound object, created boolean)
        """
        return BestAppointmentFound.objects.get_or_create(
            appointment_wanted=appointment_wanted,
            patient=patient,
            defaults={"datetime": appointment_datetime},
        )
