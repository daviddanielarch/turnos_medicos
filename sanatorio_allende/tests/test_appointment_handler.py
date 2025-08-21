import datetime
from typing import Any
from unittest.mock import patch

import pytest
from conftest import (
    TEST_DURACION_INDIVIDUAL,
    TEST_ID_ITEM_PLANTILLA,
    TEST_ID_PLANTILLA_TURNO,
)
from django.utils import timezone

from sanatorio_allende.models import BestAppointmentFound
from sanatorio_allende.services.appointment_handler import (
    AppointmentActionType,
    AppointmentHandler,
)
from sanatorio_allende.services.appointment_processor import AppointmentProcessor


class TestAppointmentHandler:
    """Test appointment handler with real database operations"""

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_creates_new_when_no_existing(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
        """Test that new appointments are created when no existing appointment"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        future_time = current_time + datetime.timedelta(days=5)

        # Process appointment
        appointment_data = {
            "datetime": future_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.CREATED
        assert result.notification_sent is True
        assert "New best appointment found" in result.message

        # Verify database was updated
        best_appointment = BestAppointmentFound.objects.get(
            appointment_wanted=find_appointment, patient=patient
        )
        assert best_appointment.datetime == future_time
        assert best_appointment.not_interested is False
        # Verify additional appointment data is stored correctly
        assert best_appointment.duracion_individual == TEST_DURACION_INDIVIDUAL
        assert best_appointment.id_plantilla_turno == TEST_ID_PLANTILLA_TURNO
        assert best_appointment.id_item_plantilla == TEST_ID_ITEM_PLANTILLA
        assert best_appointment.confirmed is False
        assert best_appointment.confirmed_at is None

        # Verify push notification was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://exp.host/--/api/v2/push/send" in call_args[0][0]

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_updates_existing_when_better(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
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
        appointment_data = {
            "datetime": better_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.UPDATED
        assert result.notification_sent is True
        assert "Better appointment found" in result.message

        # Verify database was updated
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == better_time
        # Verify additional appointment data is updated correctly
        assert existing_appointment.duracion_individual == TEST_DURACION_INDIVIDUAL
        assert existing_appointment.id_plantilla_turno == TEST_ID_PLANTILLA_TURNO
        assert existing_appointment.id_item_plantilla == TEST_ID_ITEM_PLANTILLA

        # Verify push notification was called
        mock_post.assert_called_once()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_updates_existing_when_worse(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
        """Test that worse appointments update existing one"""
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
        appointment_data = {
            "datetime": worse_time,
            "duracion_individual": 25,
            "id_plantilla_turno": 100,
            "id_item_plantilla": 299,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.UPDATED
        assert result.notification_sent is True
        assert "Better appointment found" in result.message

        # Verify database was updated
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == worse_time
        # Verify additional appointment data is updated correctly
        assert existing_appointment.duracion_individual == 25
        assert existing_appointment.id_plantilla_turno == 100
        assert existing_appointment.id_item_plantilla == 299

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_removes_existing_when_worse_even_if_outside_timeframe(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
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
        appointment_data = {
            "datetime": worse_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.REMOVED
        assert result.notification_sent is True
        assert "Removed worse appointments" in result.message

        # Verify database was updated - appointment should be deleted
        with pytest.raises(BestAppointmentFound.DoesNotExist):
            BestAppointmentFound.objects.get(id=existing_appointment.id)

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_does_nothing_when_same(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
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
        appointment_data = {
            "datetime": appointment_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.SKIPPED
        assert result.notification_sent is False
        assert "No action needed" in result.message

        # Verify database was not changed
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == appointment_time

        # Verify no push notification was sent
        mock_post.assert_not_called()

    @pytest.mark.django_db
    def test_process_appointment_skips_outside_timeframe_for_new(
        self, find_appointment: Any, patient: Any, user: Any
    ) -> None:
        """Test that appointments outside timeframe are skipped for new appointments"""
        # Set timeframe to 1 week
        find_appointment.desired_timeframe = "1 week"
        find_appointment.save()

        current_time = timezone.now()
        outside_timeframe = current_time + datetime.timedelta(days=10)

        # Process appointment outside timeframe
        appointment_data = {
            "datetime": outside_timeframe,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.SKIPPED
        assert result.notification_sent is False

        # Verify no appointment was created
        assert not BestAppointmentFound.objects.filter(
            appointment_wanted=find_appointment, patient=patient
        ).exists()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_ignores_not_interested_appointments(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
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
        appointment_data = {
            "datetime": not_interested_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.SKIPPED
        assert result.notification_sent is False

        # Verify no push notification was sent
        mock_post.assert_not_called()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_handles_multiple_not_interested(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
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
        appointment_data = {
            "datetime": not_interested_time_1,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.SKIPPED
        assert result.notification_sent is False

        # Verify no push notification was sent
        mock_post.assert_not_called()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_creates_appointment_data_correctly(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
        """Test that appointment data is created with correct information and structure"""
        # Mock successful push notification response
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_response.json = lambda: [{"status": "ok", "id": "test_receipt_id"}]
        mock_post.return_value = mock_response

        current_time = timezone.now()
        future_time = current_time + datetime.timedelta(days=5)

        # Create appointment data with all fields
        appointment_data_obj = AppointmentProcessor.create_appointment_data(
            doctor_name="Dr. Test",
            especialidad_name="Test Specialty",
            tipo_de_turno_name="Test Appointment",
            patient_dni="12345678",
            desired_timeframe="2 weeks",
            duracion_individual=TEST_DURACION_INDIVIDUAL,
            id_plantilla_turno=TEST_ID_PLANTILLA_TURNO,
            id_item_plantilla=TEST_ID_ITEM_PLANTILLA,
        )

        # Verify AppointmentData structure
        assert appointment_data_obj.doctor_name == "Dr. Test"
        assert appointment_data_obj.especialidad_name == "Test Specialty"
        assert appointment_data_obj.tipo_de_turno_name == "Test Appointment"
        assert appointment_data_obj.patient_dni == "12345678"
        assert appointment_data_obj.desired_timeframe == "2 weeks"
        assert appointment_data_obj.duracion_individual == TEST_DURACION_INDIVIDUAL
        assert appointment_data_obj.id_plantilla_turno == TEST_ID_PLANTILLA_TURNO
        assert appointment_data_obj.id_item_plantilla == TEST_ID_ITEM_PLANTILLA

        # Test with optional fields as None
        appointment_data_minimal = AppointmentProcessor.create_appointment_data(
            doctor_name="Dr. Test",
            especialidad_name="Test Specialty",
            tipo_de_turno_name="Test Appointment",
            patient_dni="12345678",
            desired_timeframe="2 weeks",
        )

        assert appointment_data_minimal.duracion_individual is None
        assert appointment_data_minimal.id_plantilla_turno is None
        assert appointment_data_minimal.id_item_plantilla is None

        # Process appointment with additional data
        appointment_data = {
            "datetime": future_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.CREATED

        # Verify database was updated with additional data
        best_appointment = BestAppointmentFound.objects.get(
            appointment_wanted=find_appointment, patient=patient
        )
        assert best_appointment.datetime == future_time
        assert best_appointment.duracion_individual == TEST_DURACION_INDIVIDUAL
        assert best_appointment.id_plantilla_turno == TEST_ID_PLANTILLA_TURNO
        assert best_appointment.id_item_plantilla == TEST_ID_ITEM_PLANTILLA
        assert best_appointment.not_interested is False
        assert best_appointment.confirmed is False
        assert best_appointment.confirmed_at is None

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
        self, mock_post: Any, find_appointment: Any, patient: Any, user: Any
    ) -> None:
        """Test that appointments are processed even without device registration"""
        current_time = timezone.now()
        future_time = current_time + datetime.timedelta(days=5)

        # Process appointment without device registration
        appointment_data = {
            "datetime": future_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.CREATED
        assert result.notification_sent is True

        # Verify database was updated
        best_appointment = BestAppointmentFound.objects.get(
            appointment_wanted=find_appointment, patient=patient
        )
        assert best_appointment.datetime == future_time
        # Verify additional appointment data is stored correctly
        assert best_appointment.duracion_individual == TEST_DURACION_INDIVIDUAL
        assert best_appointment.id_plantilla_turno == TEST_ID_PLANTILLA_TURNO
        assert best_appointment.id_item_plantilla == TEST_ID_ITEM_PLANTILLA

        mock_post.assert_not_called()

    @pytest.mark.django_db
    @patch("sanatorio_allende.services.push_notifications.requests.post")
    def test_process_appointment_updates_existing_within_timeframe(
        self,
        mock_post: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
        device_registration: Any,
    ) -> None:
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
        appointment_data = {
            "datetime": better_time,
            "duracion_individual": TEST_DURACION_INDIVIDUAL,
            "id_plantilla_turno": TEST_ID_PLANTILLA_TURNO,
            "id_item_plantilla": TEST_ID_ITEM_PLANTILLA,
        }

        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=appointment_data,
            user=user,
        )

        # Verify result
        assert result.action == AppointmentActionType.UPDATED
        assert result.notification_sent is True

        # Verify database was updated with additional data
        existing_appointment.refresh_from_db()
        assert existing_appointment.datetime == better_time
        assert existing_appointment.duracion_individual == TEST_DURACION_INDIVIDUAL
        assert existing_appointment.id_plantilla_turno == TEST_ID_PLANTILLA_TURNO
        assert existing_appointment.id_item_plantilla == TEST_ID_ITEM_PLANTILLA

        # Verify push notification was called
        mock_post.assert_called_once()

    @pytest.mark.django_db
    def test_process_appointment_no_exiting_appointment_and_null_new_appointment(
        self, find_appointment: Any, patient: Any, user: Any
    ) -> None:
        result = AppointmentHandler.process_appointment(
            appointment_to_find=find_appointment,
            patient=patient,
            new_appointment_data=None,
            user=user,
        )

        assert result.action == AppointmentActionType.SKIPPED
        assert result.notification_sent is False
        assert "No new appointment found" in result.message
