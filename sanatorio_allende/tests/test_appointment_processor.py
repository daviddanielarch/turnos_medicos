import datetime

from sanatorio_allende.services.appointment_processor import (
    AppointmentAction,
    AppointmentProcessor,
    NotificationType,
)


class TestAppointmentProcessor:
    """Test appointment processor business logic"""

    def test_new_appointment_creates_record(self) -> None:
        """Test that new appointments trigger creation action"""
        current_time = datetime.datetime.now()
        new_appointment = current_time + datetime.timedelta(days=5)

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=new_appointment,
            current_best_datetime=None,
        )

        assert result.action == AppointmentAction.CREATE_NEW
        assert result.should_notify is True
        assert result.notification_type == NotificationType.NEW

    def test_better_appointment_updates_existing(self) -> None:
        """Test that earlier appointments trigger update action"""
        current_time = datetime.datetime.now()
        existing_appointment = current_time + datetime.timedelta(days=10)
        better_appointment = current_time + datetime.timedelta(days=5)

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=better_appointment,
            current_best_datetime=existing_appointment,
        )

        assert result.action == AppointmentAction.UPDATE_EXISTING
        assert result.should_notify is True
        assert result.notification_type == NotificationType.NEW

    def test_worse_appointment_removes_existing(self) -> None:
        """Test that later appointments trigger removal action"""
        current_time = datetime.datetime.now()
        existing_appointment = current_time + datetime.timedelta(days=5)
        worse_appointment = current_time + datetime.timedelta(days=10)

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=worse_appointment,
            current_best_datetime=existing_appointment,
        )

        assert result.action == AppointmentAction.REMOVE_EXISTING
        assert result.should_notify is True
        assert result.notification_type == NotificationType.LOST

    def test_same_appointment_does_nothing(self) -> None:
        """Test that identical appointments trigger no action"""
        current_time = datetime.datetime.now()
        appointment_time = current_time + datetime.timedelta(days=5)

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=appointment_time,
            current_best_datetime=appointment_time,
        )

        assert result.action == AppointmentAction.DO_NOTHING
        assert result.should_notify is False
        assert result.notification_type == NotificationType.NONE

    def test_not_interested_appointment_ignored(self) -> None:
        """Test that appointments matching not_interested are ignored"""
        current_time = datetime.datetime.now()
        existing_appointment = current_time + datetime.timedelta(days=5)
        not_interested_time = current_time + datetime.timedelta(days=10)
        new_appointment = not_interested_time  # Same as not_interested

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=new_appointment,
            current_best_datetime=existing_appointment,
            not_interested_datetimes=[not_interested_time],
        )

        assert result.action == AppointmentAction.DO_NOTHING
        assert result.should_notify is False
        assert result.notification_type == NotificationType.NONE

    def test_not_interested_appointment_different_time_processed(self) -> None:
        """Test that not interested appointments are also removed"""
        current_time = datetime.datetime.now()
        existing_appointment = current_time + datetime.timedelta(days=15)
        not_interested_time = current_time + datetime.timedelta(days=10)
        different_appointment = current_time + datetime.timedelta(days=20)

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=different_appointment,
            current_best_datetime=existing_appointment,
            not_interested_datetimes=[not_interested_time],
        )

        assert result.action == AppointmentAction.REMOVE_EXISTING
        assert result.should_notify is True
        assert result.notification_type == NotificationType.LOST

    def test_multiple_not_interested_appointments_handled(self) -> None:
        """Test that multiple not_interested appointments are all checked"""
        current_time = datetime.datetime.now()
        existing_appointment = current_time + datetime.timedelta(days=5)
        not_interested_times = [
            current_time + datetime.timedelta(days=10),
            current_time + datetime.timedelta(days=15),
            current_time + datetime.timedelta(days=20),
        ]
        new_appointment = not_interested_times[1]  # Match second not_interested

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=new_appointment,
            current_best_datetime=existing_appointment,
            not_interested_datetimes=not_interested_times,
        )

        assert result.action == AppointmentAction.DO_NOTHING
        assert result.should_notify is False
        assert result.notification_type == NotificationType.NONE

    def test_new_appointment_with_multiple_not_interested_appointments(self) -> None:
        """Test that multiple not_interested appointments are all checked for new appointment"""
        current_time = datetime.datetime.now()
        new_appointment = current_time + datetime.timedelta(days=16)
        not_interested_times = [
            current_time + datetime.timedelta(days=10),
            current_time + datetime.timedelta(days=15),
        ]

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=new_appointment,
            current_best_datetime=None,
            not_interested_datetimes=not_interested_times,
        )

        assert result.action == AppointmentAction.CREATE_NEW
        assert result.should_notify is True
        assert result.notification_type == NotificationType.NEW

    def test_no_new_appointment_removes_existing(self) -> None:
        """Test that no new appointment removes the existing one"""
        current_time = datetime.datetime.now()
        existing_appointment = current_time + datetime.timedelta(days=5)

        result = AppointmentProcessor.compare_appointments(
            new_appointment_datetime=None,
            current_best_datetime=existing_appointment,
        )

        assert result.action == AppointmentAction.REMOVE_EXISTING
        assert result.should_notify is True
        assert result.notification_type == NotificationType.LOST
