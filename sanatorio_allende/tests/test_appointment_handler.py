import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from sanatorio_allende.models import BestAppointmentFound
from sanatorio_allende.services.appointment_handler import AppointmentHandler


class TestAppointmentHandler:
    """Test appointment handler with real database operations"""

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_creates_new_when_no_existing(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that new appointments are created when no existing appointment"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        future_time = current_time + datetime.timedelta(days=5)

        # Process appointment
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=future_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "created"
        assert result["success"] is True
        assert result["notification_sent"] is True
        assert "New best appointment found" in result["message"]

        # Verify database was updated
        best_appointment = BestAppointmentFound.objects.get(
            appointment_wanted=find_appointment, patient=patient
        )
        assert best_appointment.datetime == future_time
        assert best_appointment.not_interested is False

        # Verify push notification was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://exp.host/--/api/v2/push/send" in call_args[0][0]

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_updates_existing_when_better(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that better appointments update existing ones"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        existing_time = current_time + datetime.timedelta(days=10)
        better_time = current_time + datetime.timedelta(days=5)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=existing_time,
        )

        # Process appointment (better time)
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=better_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "updated"
        assert result["success"] is True
        assert result["notification_sent"] is True
        assert "Better appointment found" in result["message"]

        # Verify database was updated
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == better_time

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_removes_existing_when_worse(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that worse appointments remove existing ones"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        existing_time = current_time + datetime.timedelta(days=5)
        worse_time = current_time + datetime.timedelta(days=10)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=existing_time,
        )

        # Process appointment (worse time)
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=worse_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "removed"
        assert result["success"] is True
        assert result["notification_sent"] is True
        assert "Removed worse appointments" in result["message"]

        # Verify database was updated - appointment should be deleted
        with pytest.raises(BestAppointmentFound.DoesNotExist):
            BestAppointmentFound.objects.get(id=existing_appointment.id)

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_removes_existing_when_worse_even_if_outside_timeframe(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that worse appointments remove existing ones even if outside timeframe"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        # Set timeframe to 1 week
        find_appointment.desired_timeframe = "1 week"
        find_appointment.save()

        current_time = timezone.now()
        existing_time = current_time + datetime.timedelta(days=5)
        worse_time = current_time + datetime.timedelta(days=20)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=existing_time,
        )

        # Process appointment (worse time)
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=worse_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "removed"
        assert result["success"] is True
        assert result["notification_sent"] is True
        assert "Removed worse appointments" in result["message"]

        # Verify database was updated - appointment should be deleted
        with pytest.raises(BestAppointmentFound.DoesNotExist):
            BestAppointmentFound.objects.get(id=existing_appointment.id)

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_does_nothing_when_same(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that same appointments trigger no action"""
        current_time = timezone.now()
        appointment_time = current_time + datetime.timedelta(days=5)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=appointment_time,
        )

        # Process appointment (same time)
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=appointment_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "none"
        assert result["success"] is True
        assert result["notification_sent"] is False
        assert "No action needed" in result["message"]

        # Verify database was not changed
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == appointment_time

        # Verify no push notification was sent
        mock_post.assert_not_called()

    @pytest.mark.django_db
    def test_process_appointment_skips_outside_timeframe_for_new(
        self, find_appointment, patient, user
    ):
        """Test that appointments outside timeframe are skipped for new appointments"""
        # Set timeframe to 1 week
        find_appointment.desired_timeframe = "1 week"
        find_appointment.save()

        current_time = timezone.now()
        outside_timeframe = current_time + datetime.timedelta(days=10)

        # Process appointment outside timeframe
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=outside_timeframe,
            user=user,
        )

        # Verify result
        assert result["action"] == "skipped"
        assert result["success"] is False
        assert result["notification_sent"] is False
        assert "outside desired timeframe" in result["message"]

        # Verify no appointment was created
        assert not BestAppointmentFound.objects.filter(
            appointment_wanted=find_appointment, patient=patient
        ).exists()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_ignores_not_interested_appointments(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that not_interested appointments are ignored"""
        current_time = timezone.now()
        existing_time = current_time + datetime.timedelta(days=5)
        not_interested_time = current_time + datetime.timedelta(days=10)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=existing_time,
        )

        # Create not_interested appointment
        not_interested_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=not_interested_time,
            not_interested=True,
        )

        # Process appointment matching not_interested time
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=not_interested_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "none"
        assert result["success"] is True
        assert result["notification_sent"] is False

        # Verify no push notification was sent
        mock_post.assert_not_called()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_handles_multiple_not_interested(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that multiple not_interested appointments are handled correctly"""
        current_time = timezone.now()
        existing_time = current_time + datetime.timedelta(days=5)
        not_interested_time_1 = current_time + datetime.timedelta(days=10)
        not_interested_time_2 = current_time + datetime.timedelta(days=15)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=existing_time,
        )

        # Create multiple not_interested appointments
        not_interested_1 = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=not_interested_time_1,
            not_interested=True,
        )
        not_interested_2 = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=not_interested_time_2,
            not_interested=True,
        )

        # Process appointment matching one of the not_interested times
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=not_interested_time_1,
            user=user,
        )

        # Verify result
        assert result["action"] == "none"
        assert result["success"] is True
        assert result["notification_sent"] is False

        # Verify no push notification was sent
        mock_post.assert_not_called()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_creates_appointment_data_correctly(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that appointment data is created with correct information"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        future_time = current_time + datetime.timedelta(days=5)

        # Process appointment
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=future_time,
            user=user,
        )

        # Verify push notification was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify the notification payload contains correct appointment data
        payload = call_args[1]["data"]
        import json

        notification_data = json.loads(payload)

        # Check that the notification contains appointment information
        assert len(notification_data) == 1  # Single notification
        notification = notification_data[0]
        assert notification["to"] == "test_push_token_123"
        assert "Dr. Juan Pérez" in notification["title"]
        assert "Cardiología" in notification["body"]
        assert "CONSULTA" in notification["body"]

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_with_no_device_registration(
        self, mock_post, find_appointment, patient, user
    ):
        """Test that appointments are processed even without device registration"""
        current_time = timezone.now()
        future_time = current_time + datetime.timedelta(days=5)

        # Process appointment without device registration
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=future_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "created"
        assert result["success"] is True
        assert result["notification_sent"] is True

        # Verify database was updated
        best_appointment = BestAppointmentFound.objects.get(
            appointment_wanted=find_appointment, patient=patient
        )
        assert best_appointment.datetime == future_time

        mock_post.assert_not_called()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_updates_existing_within_timeframe(
        self, mock_post, find_appointment, patient, user, device_registration
    ):
        """Test that better appointments within timeframe update existing ones"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        existing_time = current_time + datetime.timedelta(days=10)
        better_time = current_time + datetime.timedelta(days=5)

        # Create existing appointment
        existing_appointment = BestAppointmentFound.objects.create(
            patient=patient,
            appointment_wanted=find_appointment,
            datetime=existing_time,
        )

        # Process appointment (better time within 2 weeks timeframe)
        result = AppointmentHandler.process_appointment(
            appointment=find_appointment,
            patient=patient,
            new_appointment_datetime=better_time,
            user=user,
        )

        # Verify result
        assert result["action"] == "updated"
        assert result["success"] is True
        assert result["notification_sent"] is True

        # Verify database was updated
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == better_time
