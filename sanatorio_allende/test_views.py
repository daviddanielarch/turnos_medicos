import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from .models import (AppointmentType, BestAppointmentFound, DeviceRegistration,
                     Doctor, Especialidad, FindAppointment, PacienteAllende)


@pytest.fixture
def user():
    """Create a test user"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def client(user):
    """Django test client fixture with authenticated user"""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def evil_user():
    """Create a test user"""
    return User.objects.create_user(
        username="eviluser", email="evil@example.com", password="evilpass123"
    )


@pytest.fixture
def evil_client(evil_user):
    """Django test client fixture with authenticated user"""
    client = Client()
    client.force_login(evil_user)
    return client


@pytest.fixture
def especialidad():
    """Create a test especialidad"""
    return Especialidad.objects.create(
        name="Cardiología",
        id_especialidad=1,
        id_servicio=1,
        id_sucursal=1,
        sucursal="Centro",
        servicio="Cardiología",
    )


@pytest.fixture
def doctor(especialidad):
    """Create a test doctor"""
    return Doctor.objects.create(
        name="Dr. Juan Pérez",
        id_recurso=1,
        id_tipo_recurso=1,
        especialidad=especialidad,
    )


@pytest.fixture
def appointment_type(especialidad):
    """Create a test appointment type"""
    return AppointmentType.objects.create(
        name="CONSULTA", id_tipo_turno=5495, especialidad=especialidad
    )


@pytest.fixture
def patient(user):
    """Create a test patient"""
    return PacienteAllende.objects.create(
        user=user,
        name="Juan Pérez",
        id_paciente="12345",
        docid="12345678",
        password="testpass123",
    )


@pytest.fixture
def find_appointment(doctor, appointment_type, patient):
    """Create a test find appointment"""
    return FindAppointment.objects.create(
        doctor=doctor, tipo_de_turno=appointment_type, patient=patient, active=True
    )


@pytest.fixture
def best_appointment_found(find_appointment, patient):
    """Create a test best appointment found"""
    return BestAppointmentFound.objects.create(
        appointment_wanted=find_appointment, patient=patient, datetime=timezone.now()
    )


@pytest.fixture
def device_registration(user):
    """Create a test device registration"""
    return DeviceRegistration.objects.create(
        user=user, push_token="test_push_token_123", platform="expo", is_active=True
    )


class TestDoctorListView:
    """Test cases for DoctorListView"""

    @pytest.mark.django_db
    def test_get_doctors_success(self, client, doctor):
        """Test successful GET request to list doctors"""
        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["doctors"]) == 1
        assert data["doctors"][0]["name"] == doctor.name
        assert data["doctors"][0]["especialidad"] == doctor.especialidad.name
        assert data["doctors"][0]["location"] == doctor.especialidad.sucursal

    @pytest.mark.django_db
    def test_get_doctors_empty(self, client):
        """Test GET request when no doctors exist"""
        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["doctors"]) == 0


class TestAppointmentTypeListView:
    """Test cases for AppointmentTypeListView"""

    @pytest.mark.django_db
    def test_get_appointment_types_success(self, client, doctor, appointment_type):
        """Test successful GET request to list appointment types"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(url, {"doctor_id": doctor.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["appointment_types"]) == 1
        assert data["appointment_types"][0]["name"] == appointment_type.name
        assert (
            data["appointment_types"][0]["id_tipo_turno"]
            == appointment_type.id_tipo_turno
        )
        assert (
            data["appointment_types"][0]["description"]
            == f"{appointment_type.name} appointment"
        )

    @pytest.mark.django_db
    def test_get_appointment_types_missing_doctor_id(self, client):
        """Test GET request without doctor_id parameter"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(url)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "doctor_id parameter is required" in data["error"]

    @pytest.mark.django_db
    def test_get_appointment_types_doctor_not_found(self, client):
        """Test GET request with non-existent doctor_id"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(url, {"doctor_id": 999})

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_get_appointment_types_empty(self, client, doctor):
        """Test GET request when no appointment types exist for doctor"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(url, {"doctor_id": doctor.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["appointment_types"]) == 0


class TestFindAppointmentView:
    """Test cases for FindAppointmentView"""

    @pytest.mark.django_db
    def test_get_find_appointments_for_other_user(self, evil_client, find_appointment):
        """Test successful GET request to list find appointments"""
        url = reverse("sanatorio_allende:api_find_appointments")
        response = evil_client.get(url, {"patient_id": find_appointment.patient.id})

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_find_appointments_success(self, client, find_appointment):
        """Test successful GET request to list find appointments"""
        url = reverse("sanatorio_allende:api_find_appointments")
        response = client.get(url, {"patient_id": find_appointment.patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["appointments"]) == 1
        assert data["appointments"][0]["name"] == find_appointment.doctor.name
        assert data["appointments"][0]["enabled"] == find_appointment.active
        assert (
            data["appointments"][0]["especialidad"]
            == find_appointment.doctor.especialidad.name
        )
        assert (
            data["appointments"][0]["location"]
            == find_appointment.doctor.especialidad.sucursal
        )
        assert (
            data["appointments"][0]["tipo_de_turno"]
            == find_appointment.tipo_de_turno.name
        )
        assert data["appointments"][0]["doctor_id"] == find_appointment.doctor.id
        assert (
            data["appointments"][0]["tipo_de_turno_id"]
            == find_appointment.tipo_de_turno.id
        )
        assert (
            data["appointments"][0]["desired_timeframe"]
            == find_appointment.desired_timeframe
        )

    @pytest.mark.django_db
    def test_post_create_appointment_for_other_user(
        self, evil_client, doctor, appointment_type, patient
    ):
        """Test POST request for other user"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": doctor.id,
            "appointment_type_id": appointment_type.id,
            "patient_id": patient.id,
        }
        response = evil_client.post(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_post_create_appointment_success(
        self, client, doctor, appointment_type, patient
    ):
        """Test successful POST request to create appointment"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": doctor.id,
            "appointment_type_id": appointment_type.id,
            "patient_id": patient.id,
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Appointment created successfully" in data["message"]
        assert "appointment_id" in data

        created_appointment = FindAppointment.objects.get(id=data["appointment_id"])
        assert created_appointment.doctor == doctor
        assert created_appointment.tipo_de_turno == appointment_type
        assert created_appointment.patient == patient
        assert created_appointment.active is True
        assert created_appointment.desired_timeframe == "anytime"

    @pytest.mark.django_db
    def test_post_create_appointment_missing_parameters(self, client):
        """Test POST request with missing parameters"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {"doctor_id": 1, "appointment_type_id": 1}  # Missing patient_id
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert (
            "doctor_id, appointment_type_id, and patient_id are required"
            in data["error"]
        )

    @pytest.mark.django_db
    def test_post_create_appointment_doctor_not_found(
        self, client, appointment_type, patient
    ):
        """Test POST request with non-existent doctor"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": 999,
            "appointment_type_id": appointment_type.id,
            "patient_id": patient.id,
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_post_create_appointment_type_not_found(self, client, doctor, patient):
        """Test POST request with non-existent appointment type"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": doctor.id,
            "appointment_type_id": 999,
            "patient_id": patient.id,
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_post_create_appointment_patient_not_found(
        self, client, doctor, appointment_type
    ):
        """Test POST request with non-existent patient"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": doctor.id,
            "appointment_type_id": appointment_type.id,
            "patient_id": 999,
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_patch_update_appointment_for_other_user(
        self, evil_client, find_appointment
    ):
        """Test PATCH request for other user"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "appointment_id": find_appointment.id,
            "active": False,
            "patient_id": find_appointment.patient.id,
        }
        response = evil_client.patch(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_patch_update_appointment_status_success(self, client, find_appointment):
        """Test successful PATCH request to update appointment status"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "appointment_id": find_appointment.id,
            "active": False,
            "patient_id": find_appointment.patient.id,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "inactive" in data["message"]

        # Verify the appointment was actually updated
        find_appointment.refresh_from_db()
        assert find_appointment.active is False

    @pytest.mark.django_db
    def test_patch_update_appointment_missing_parameters(self, client):
        """Test PATCH request with missing parameters"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {"appointment_id": 1}  # Missing active
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "appointment_id and active parameters are required" in data["error"]

    @pytest.mark.django_db
    def test_patch_update_appointment_not_found(self, client, patient):
        """Test PATCH request with non-existent appointment"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "appointment_id": 999,
            "active": False,
            "patient_id": patient.id,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_post_create_appointment_with_desired_timeframe(
        self, client, doctor, appointment_type, patient
    ):
        """Test successful POST request to create appointment with desired_timeframe"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": doctor.id,
            "appointment_type_id": appointment_type.id,
            "patient_id": patient.id,
            "desired_timeframe": "2 weeks",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Appointment created successfully" in data["message"]
        assert "appointment_id" in data

        created_appointment = FindAppointment.objects.get(id=data["appointment_id"])
        assert created_appointment.doctor == doctor
        assert created_appointment.tipo_de_turno == appointment_type
        assert created_appointment.patient == patient
        assert created_appointment.active is True
        assert created_appointment.desired_timeframe == "2 weeks"

    @pytest.mark.django_db
    def test_post_update_existing_appointment_change_timeframe(
        self, client, find_appointment
    ):
        """Test POST request changes existing appointment's desired_timeframe"""
        # Set initial desired_timeframe
        find_appointment.desired_timeframe = "3 weeks"
        find_appointment.save()

        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": find_appointment.doctor.id,
            "appointment_type_id": find_appointment.tipo_de_turno.id,
            "patient_id": find_appointment.patient.id,
            "desired_timeframe": "2 weeks",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Appointment updated successfully" in data["message"]

        # Verify the appointment was updated
        find_appointment.refresh_from_db()
        assert find_appointment.desired_timeframe == "2 weeks"

    @pytest.mark.django_db
    def test_post_create_appointment_invalid_timeframe(
        self, client, doctor, appointment_type, patient
    ):
        """Test POST request with invalid desired_timeframe value"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "doctor_id": doctor.id,
            "appointment_type_id": appointment_type.id,
            "patient_id": patient.id,
            "desired_timeframe": "invalid_timeframe",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        # The view should still accept the request since validation is handled at model level
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        created_appointment = FindAppointment.objects.get(id=data["appointment_id"])
        assert created_appointment.desired_timeframe == "invalid_timeframe"


class TestBestAppointmentListView:
    """Test cases for BestAppointmentListView"""

    @pytest.mark.django_db
    def test_get_best_appointments_success(self, client, best_appointment_found):
        """Test successful GET request to list best appointments"""
        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": best_appointment_found.patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["best_appointments"]) == 1
        appointment = best_appointment_found.appointment_wanted
        assert data["best_appointments"][0]["doctor_name"] == appointment.doctor.name
        assert (
            data["best_appointments"][0]["especialidad"]
            == appointment.doctor.especialidad.name
        )
        assert (
            data["best_appointments"][0]["location"]
            == appointment.doctor.especialidad.sucursal
        )
        assert (
            data["best_appointments"][0]["tipo_de_turno"]
            == appointment.tipo_de_turno.name
        )
        assert "best_datetime" in data["best_appointments"][0]

    @pytest.mark.django_db
    def test_get_best_appointments_appointment_for_other_user(
        self, evil_client, best_appointment_found
    ):
        """Test successful GET request to list best appointments"""
        url = reverse("sanatorio_allende:api_best_appointments")
        response = evil_client.get(
            url, {"patient_id": best_appointment_found.patient.id}
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_best_appointments_empty(self, client, patient):
        """Test GET request when no best appointments exist"""
        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["best_appointments"]) == 0


class TestPatientListView:
    """Test cases for PatientListView"""

    @pytest.mark.django_db
    def test_get_patients_success(self, client, patient):
        """Test successful GET request to list patients"""
        url = reverse("sanatorio_allende:api_patients")
        response = client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["patients"]) == 1
        assert data["patients"][0]["name"] == patient.name
        assert data["patients"][0]["id_paciente"] == patient.id_paciente
        assert data["patients"][0]["docid"] == patient.docid
        assert "updated_at" in data["patients"][0]

    @pytest.mark.django_db
    def test_get_patients_empty(self, client):
        """Test GET request when no patients exist"""
        url = reverse("sanatorio_allende:api_patients")
        response = client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["patients"]) == 0

    @pytest.mark.django_db
    @patch("sanatorio_allende.appointments.requests.post")
    def test_post_create_patient_success(self, mock_post, client):
        """Test successful POST request to create patient"""
        # Mock the requests.post call in Allende.validate_credentials
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_patients")
        data = {
            "name": "María García",
            "id_paciente": "67890",
            "docid": "87654321",
            "password": "testpass456",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Patient created successfully" in data["message"]
        assert "patient_id" in data

        created_patient = PacienteAllende.objects.get(id=data["patient_id"])
        assert created_patient.name == "María García"
        assert created_patient.id_paciente is None
        assert created_patient.docid == "87654321"
        assert created_patient.password == "testpass456"

        # Verify the mock was called with the expected parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://miportal.sanatorioallende.com/backend/Token"
        assert (
            call_args[1]["data"]["NumeroDocumento"] == "ODc2NTQzMjE="
        )  # base64 encoded docid
        assert (
            call_args[1]["data"]["Password"] == "dGVzdHBhc3M0NTY="
        )  # base64 encoded password

    @pytest.mark.django_db
    @patch("sanatorio_allende.appointments.requests.post")
    def test_post_create_patient_invalid_credentials(self, mock_post, client):
        """Test successful POST request to create patient"""
        # Mock the requests.post call in Allende.validate_credentials
        mock_response = type("MockResponse", (), {"status_code": 400})()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_patients")
        data = {
            "name": "María García",
            "id_paciente": "67890",
            "docid": "87654321",
            "password": "testpass456",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_post_create_patient_missing_parameters(self, client):
        """Test POST request with missing parameters"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"name": "Test Patient"}  # Missing docid and password
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "name, docid, and password are required" in data["error"]

    @pytest.mark.django_db
    @patch("sanatorio_allende.appointments.requests.post")
    def test_post_create_patient_already_exists(self, mock_post, client, patient):
        """Test POST request when patient with same docid already exists"""
        mock_response = type("MockResponse", (), {"status_code": 200})()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_patients")
        data = {
            "name": "Different Name",
            "id_paciente": "99999",
            "docid": patient.docid,  # Same docid as existing patient
            "password": "testpass789",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Patient already exists with this document ID" in data["error"]

    @pytest.mark.django_db
    def test_delete_patient_success(self, client, patient):
        """Test successful DELETE request to delete patient"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"patient_id": patient.id}
        response = client.delete(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Patient deleted successfully" in data["message"]

        # Verify the patient was actually deleted
        with pytest.raises(PacienteAllende.DoesNotExist):
            PacienteAllende.objects.get(id=patient.id)

    @pytest.mark.django_db
    def test_delete_patient_missing_patient_id(self, client):
        """Test DELETE request without patient_id parameter"""
        url = reverse("sanatorio_allende:api_patients")
        data = {}  # Missing patient_id
        response = client.delete(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "patient_id is required" in data["error"]

    @pytest.mark.django_db
    def test_delete_patient_not_found(self, client):
        """Test DELETE request with non-existent patient_id"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"patient_id": 999}
        response = client.delete(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Patient not found" in data["error"]

    @pytest.mark.django_db
    def test_delete_patient_for_other_user(self, evil_client, patient):
        """Test DELETE request for patient belonging to another user"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"patient_id": patient.id}
        response = evil_client.delete(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 404


class TestDeviceRegistrationView:
    """Test cases for DeviceRegistrationView"""

    @pytest.mark.django_db
    def test_post_register_device_new(self, client):
        """Test successful POST request to register new device"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {
            "push_token": "new_push_token_123",
            "platform": "expo",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Device registered successfully" in data["message"]
        assert data["created"] is True

    @pytest.mark.django_db
    def test_post_register_device_existing(self, client, device_registration):
        """Test POST request to update existing device"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {
            "push_token": device_registration.push_token,
            "platform": "ios",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Device registered successfully" in data["message"]
        assert data["created"] is False

        # Verify the device was updated
        device_registration.refresh_from_db()
        assert device_registration.platform == "ios"
        assert device_registration.is_active is True

    @pytest.mark.django_db
    def test_post_register_device_missing_token(self, client):
        """Test POST request without push_token"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {"platform": "expo"}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "push_token is required" in data["error"]

    @pytest.mark.django_db
    def test_post_register_device_default_platform(self, client):
        """Test POST request with default platform"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {"push_token": "test_token_123"}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        # Verify default platform was used
        device = DeviceRegistration.objects.get(push_token="test_token_123")
        assert device.platform == "expo"
