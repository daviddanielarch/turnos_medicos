import json
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from conftest import (
    TEST_CONFIRMED_ID_TURNO,
    TEST_DURACION_INDIVIDUAL,
    TEST_ESPECIALIDAD_ID,
    TEST_FINANCIADOR_ID,
    TEST_ITEM_PLANTILLA_ID,
    TEST_PATIENT_ID,
    TEST_PLAN_ID,
    TEST_PLANTILLA_TURNO_ID,
    TEST_PRESTACION_ID,
    TEST_RECURSO_ID,
    TEST_SERVICIO_ID,
    TEST_SUCURSAL_ID,
    TEST_TIPO_PRESTACION_ID,
    TEST_TIPO_RECURSO_ID,
    TEST_TIPO_TURNO_ID,
)
from django.urls import reverse
from django.utils import timezone

from sanatorio_allende.models import (
    BestAppointmentFound,
    DeviceRegistration,
    FindAppointment,
    PacienteAllende,
)


class TestDoctorListView:
    """Test cases for DoctorListView"""

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_get_doctors_success(
        self, mock_post: Any, client: Any, patient: PacienteAllende
    ) -> None:
        """Test successful GET request to list doctors"""
        # Mock the Allende API response
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: {
                    "Especialidades": [],
                    "Profesionales": [
                        {
                            "IdRecurso": TEST_RECURSO_ID,
                            "IdTipoRecurso": TEST_TIPO_RECURSO_ID,
                            "NumeroMatricula": 12345,
                            "Nombre": "Dr. Juan Pérez",
                            "IdEspecialidad": TEST_ESPECIALIDAD_ID,
                            "Especialidad": "Cardiología",
                            "IdServicio": TEST_SERVICIO_ID,
                            "Servicio": "Cardiología",
                            "IdSucursal": TEST_SUCURSAL_ID,
                            "Sucursal": "Centro",
                        }
                    ],
                },
            },
        )()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url, {"patient_id": patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "doctors" in data
        assert len(data["doctors"]["Profesionales"]) == 1
        assert data["doctors"]["Profesionales"][0]["Nombre"] == "Dr. Juan Pérez"
        assert data["doctors"]["Profesionales"][0]["Especialidad"] == "Cardiología"
        assert data["doctors"]["Profesionales"][0]["Sucursal"] == "Centro"

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_get_doctors_with_pattern(
        self, mock_post: Any, client: Any, patient: PacienteAllende
    ) -> None:
        """Test GET request with pattern parameter"""
        # Mock the Allende API response
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: {"Especialidades": [], "Profesionales": []},
            },
        )()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url, {"pattern": "cardio", "patient_id": patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "doctors" in data

        # Verify the pattern was passed to the API
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "Criterio" in call_args[1]["json"]
        assert call_args[1]["json"]["Criterio"] == "cardio"

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_get_doctors_empty(
        self, mock_post: Any, client: Any, patient: PacienteAllende
    ) -> None:
        """Test GET request when no doctors exist"""
        # Mock the Allende API response
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: {"Especialidades": [], "Profesionales": []},
            },
        )()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url, {"patient_id": patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "doctors" in data
        assert len(data["doctors"]["Profesionales"]) == 0


class TestAppointmentTypeListView:
    """Test cases for AppointmentTypeListView"""

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.get")
    def test_get_appointment_types_success(
        self, mock_get: Any, client: Any, patient: PacienteAllende
    ) -> None:
        """Test successful GET request to list appointment types"""
        # Mock the Allende API response
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: [
                    {
                        "IdTipoPrestacion": TEST_TIPO_TURNO_ID,
                        "Activo": True,
                        "HabilitadaTelemedicina": False,
                        "Prefacturables": "420101-CONSULTA MEDICA\n",
                        "Id": TEST_TIPO_PRESTACION_ID,
                        "Nombre": "CONSULTA",
                    }
                ],
            },
        )()
        mock_get.return_value = mock_response

        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(
            url,
            {
                "patient_id": patient.id,
                "id_especialidad": str(TEST_ESPECIALIDAD_ID),
                "id_servicio": str(TEST_SERVICIO_ID),
                "id_sucursal": str(TEST_SUCURSAL_ID),
            },
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["appointment_types"]) == 1
        assert data["appointment_types"][0]["Nombre"] == "CONSULTA"
        assert data["appointment_types"][0]["IdTipoPrestacion"] == TEST_TIPO_TURNO_ID
        assert data["appointment_types"][0]["Id"] == TEST_TIPO_PRESTACION_ID

    @pytest.mark.django_db
    def test_get_appointment_types_missing_parameters(
        self, client: Any, patient: PacienteAllende
    ) -> None:
        """Test GET request without required parameters"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(url, {"patient_id": patient.id})

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert (
            "id_especialidad, id_servicio, and id_sucursal are required"
            in data["error"]
        )

    @pytest.mark.django_db
    def test_get_appointment_types_missing_id_especialidad(
        self, client: Any, patient: PacienteAllende
    ) -> None:
        """Test GET request without id_especialidad parameter"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(
            url,
            {
                "patient_id": patient.id,
                "id_servicio": str(TEST_SERVICIO_ID),
                "id_sucursal": str(TEST_SUCURSAL_ID),
            },
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert (
            "id_especialidad, id_servicio, and id_sucursal are required"
            in data["error"]
        )

    @pytest.mark.django_db
    def test_get_appointment_types_missing_id_servicio(
        self, client: Any, patient: PacienteAllende
    ) -> None:
        """Test GET request without id_servicio parameter"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(
            url,
            {
                "patient_id": patient.id,
                "id_especialidad": str(TEST_ESPECIALIDAD_ID),
                "id_sucursal": str(TEST_SUCURSAL_ID),
            },
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert (
            "id_especialidad, id_servicio, and id_sucursal are required"
            in data["error"]
        )

    @pytest.mark.django_db
    def test_get_appointment_types_missing_id_sucursal(
        self, client: Any, patient: PacienteAllende
    ) -> None:
        """Test GET request without id_sucursal parameter"""
        url = reverse("sanatorio_allende:api_appointment_types")
        response = client.get(
            url,
            {
                "patient_id": patient.id,
                "id_especialidad": str(TEST_ESPECIALIDAD_ID),
                "id_servicio": str(TEST_SERVICIO_ID),
            },
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert (
            "id_especialidad, id_servicio, and id_sucursal are required"
            in data["error"]
        )


class TestFindAppointmentView:
    """Test cases for FindAppointmentView"""

    @pytest.mark.django_db
    def test_get_find_appointments_for_other_user(
        self, evil_client: Any, find_appointment: Any
    ) -> None:
        """Test successful GET request to list find appointments"""
        url = reverse("sanatorio_allende:api_find_appointments")
        response = evil_client.get(url, {"patient_id": find_appointment.patient.id})

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_find_appointments_success(
        self, client: Any, find_appointment: Any
    ) -> None:
        """Test successful GET request to list find appointments"""
        url = reverse("sanatorio_allende:api_find_appointments")
        response = client.get(url, {"patient_id": find_appointment.patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["appointments"]) == 1
        assert data["appointments"][0]["name"] == find_appointment.doctor_name
        assert data["appointments"][0]["enabled"] == find_appointment.active
        assert data["appointments"][0]["especialidad"] == find_appointment.especialidad
        assert data["appointments"][0]["location"] == find_appointment.sucursal
        assert (
            data["appointments"][0]["tipo_de_turno"]
            == find_appointment.nombre_tipo_prestacion
        )

        assert data["appointments"][0]["doctor_id"] == find_appointment.id_recurso
        assert (
            data["appointments"][0]["tipo_de_turno_id"]
            == find_appointment.id_tipo_prestacion
        )
        assert (
            data["appointments"][0]["desired_timeframe"]
            == find_appointment.desired_timeframe
        )

    @pytest.mark.django_db
    def test_post_create_appointment_for_other_user(
        self, evil_client: Any, patient: Any
    ) -> None:
        """Test POST request for other user"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "id_servicio": TEST_SERVICIO_ID,
            "id_sucursal": TEST_SUCURSAL_ID,
            "id_recurso": TEST_RECURSO_ID,
            "id_especialidad": TEST_ESPECIALIDAD_ID,
            "id_tipo_recurso": TEST_TIPO_RECURSO_ID,
            "id_prestacion": TEST_PRESTACION_ID,
            "id_tipo_prestacion": TEST_TIPO_PRESTACION_ID,
            "nombre_tipo_prestacion": "CONSULTA",
            "patient_id": patient.id,
            "doctor_name": "Dr. Juan Pérez",
            "servicio": "Cardiología",
            "sucursal": "Centro",
            "especialidad": "Cardiología",
        }
        response = evil_client.post(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_post_create_appointment_success(self, client: Any, patient: Any) -> None:
        """Test successful POST request to create appointment"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "id_servicio": TEST_SERVICIO_ID,
            "id_sucursal": TEST_SUCURSAL_ID,
            "id_recurso": TEST_RECURSO_ID,
            "id_especialidad": TEST_ESPECIALIDAD_ID,
            "id_tipo_recurso": TEST_TIPO_RECURSO_ID,
            "id_prestacion": TEST_PRESTACION_ID,
            "id_tipo_prestacion": TEST_TIPO_PRESTACION_ID,
            "nombre_tipo_prestacion": "CONSULTA",
            "patient_id": patient.id,
            "doctor_name": "Dr. Juan Pérez",
            "servicio": "Cardiología",
            "sucursal": "Centro",
            "especialidad": "Cardiología",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert "Appointment created successfully" in data["message"]
        assert "appointment_id" in data

        created_appointment = FindAppointment.objects.get(id=data["appointment_id"])
        assert created_appointment.doctor_name == "Dr. Juan Pérez"
        assert created_appointment.id_servicio == TEST_SERVICIO_ID
        assert created_appointment.id_sucursal == TEST_SUCURSAL_ID
        assert created_appointment.id_recurso == TEST_RECURSO_ID
        assert created_appointment.id_especialidad == TEST_ESPECIALIDAD_ID
        assert created_appointment.id_tipo_recurso == TEST_TIPO_RECURSO_ID
        assert created_appointment.id_prestacion == TEST_PRESTACION_ID
        assert created_appointment.id_tipo_prestacion == TEST_TIPO_PRESTACION_ID
        assert created_appointment.nombre_tipo_prestacion == "CONSULTA"
        assert created_appointment.patient == patient
        assert created_appointment.active is True
        assert created_appointment.desired_timeframe == "anytime"

    @pytest.mark.django_db
    def test_post_create_appointment_missing_parameters(self, client: Any) -> None:
        """Test POST request with missing parameters"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "id_servicio": TEST_SERVICIO_ID,
            "id_sucursal": TEST_SUCURSAL_ID,
            "id_recurso": TEST_RECURSO_ID,
            "id_especialidad": TEST_ESPECIALIDAD_ID,
            "id_tipo_recurso": TEST_TIPO_RECURSO_ID,
            # Missing id_prestacion, id_tipo_prestacion and nombre_tipo_prestacion
            "patient_id": 1,
            "doctor_name": "Dr. Juan Pérez",
            "servicio": "Cardiología",
            "sucursal": "Centro",
            "especialidad": "Cardiología",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert (
            "id_servicio, id_sucursal, id_recurso, id_especialidad, id_tipo_recurso, id_prestacion, id_tipo_prestacion, and nombre_tipo_prestacion are required"
            in response_data["error"]
        )

    @pytest.mark.django_db
    def test_post_create_appointment_patient_not_found(self, client: Any) -> None:
        """Test POST request with non-existent patient"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "id_servicio": TEST_SERVICIO_ID,
            "id_sucursal": TEST_SUCURSAL_ID,
            "id_recurso": TEST_RECURSO_ID,
            "id_especialidad": TEST_ESPECIALIDAD_ID,
            "id_tipo_recurso": TEST_TIPO_RECURSO_ID,
            "id_prestacion": TEST_PRESTACION_ID,
            "id_tipo_prestacion": TEST_TIPO_PRESTACION_ID,
            "nombre_tipo_prestacion": "CONSULTA",
            "patient_id": 999,
            "doctor_name": "Dr. Juan Pérez",
            "servicio": "Cardiología",
            "sucursal": "Centro",
            "especialidad": "Cardiología",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_post_create_appointment_existing_appointment(
        self, client: Any, find_appointment: Any
    ) -> None:
        """Test POST request when appointment already exists"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "id_servicio": find_appointment.id_servicio,
            "id_sucursal": find_appointment.id_sucursal,
            "id_recurso": find_appointment.id_recurso,
            "id_especialidad": find_appointment.id_especialidad,
            "id_tipo_recurso": find_appointment.id_tipo_recurso,
            "id_prestacion": find_appointment.id_prestacion,
            "id_tipo_prestacion": find_appointment.id_tipo_prestacion,
            "nombre_tipo_prestacion": find_appointment.nombre_tipo_prestacion,
            "patient_id": find_appointment.patient.id,
            "doctor_name": find_appointment.doctor_name,
            "servicio": find_appointment.servicio,
            "sucursal": find_appointment.sucursal,
            "especialidad": find_appointment.especialidad,
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
        self, client: Any, patient: Any
    ) -> None:
        """Test POST request with invalid desired_timeframe value"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "id_servicio": TEST_SERVICIO_ID,
            "id_sucursal": TEST_SUCURSAL_ID,
            "id_recurso": TEST_RECURSO_ID,
            "id_especialidad": TEST_ESPECIALIDAD_ID,
            "id_tipo_recurso": TEST_TIPO_RECURSO_ID,
            "id_prestacion": TEST_PRESTACION_ID,
            "id_tipo_prestacion": TEST_TIPO_PRESTACION_ID,
            "nombre_tipo_prestacion": "CONSULTA",
            "patient_id": patient.id,
            "doctor_name": "Dr. Juan Pérez",
            "servicio": "Cardiología",
            "sucursal": "Centro",
            "especialidad": "Cardiología",
            "desired_timeframe": "invalid_timeframe",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        # The view should still accept the request since validation is handled at model level
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        created_appointment = FindAppointment.objects.get(id=data["appointment_id"])
        assert created_appointment.desired_timeframe == "invalid_timeframe"

    @pytest.mark.django_db
    def test_patch_update_appointment_for_other_user(
        self, evil_client: Any, find_appointment: Any
    ) -> None:
        """Test PATCH request for other user"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "appointment_id": find_appointment.id,
            "active": False,
        }
        response = evil_client.patch(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_patch_update_appointment_status_success(
        self, client: Any, find_appointment: Any
    ) -> None:
        """Test successful PATCH request to update appointment status"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "appointment_id": find_appointment.id,
            "active": False,
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
    def test_patch_update_appointment_missing_parameters(self, client: Any) -> None:
        """Test PATCH request with missing parameters"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {"appointment_id": 1}  # Missing active
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert (
            "appointment_id and active parameters are required"
            in response_data["error"]
        )

    @pytest.mark.django_db
    def test_patch_update_appointment_not_found(self, client: Any) -> None:
        """Test PATCH request with non-existent appointment"""
        url = reverse("sanatorio_allende:api_find_appointments")
        data = {
            "appointment_id": 999,
            "active": False,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404


class TestBestAppointmentListView:
    """Test cases for BestAppointmentListView"""

    @pytest.mark.django_db
    def test_get_best_appointments_success(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test successful GET request to list best appointments"""
        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": best_appointment_found.patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["best_appointments"]) == 1
        appointment = best_appointment_found.appointment_wanted
        assert data["best_appointments"][0]["doctor_name"] == appointment.doctor_name
        assert data["best_appointments"][0]["especialidad"] == appointment.especialidad
        assert data["best_appointments"][0]["location"] == appointment.sucursal
        assert (
            data["best_appointments"][0]["tipo_de_turno"]
            == appointment.nombre_tipo_prestacion
        )
        assert "best_datetime" in data["best_appointments"][0]

    @pytest.mark.django_db
    def test_get_best_appointments_appointment_for_other_user(
        self, evil_client: Any, best_appointment_found: Any
    ) -> None:
        """Test successful GET request to list best appointments"""
        url = reverse("sanatorio_allende:api_best_appointments")
        response = evil_client.get(
            url, {"patient_id": best_appointment_found.patient.id}
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_best_appointments_empty(self, client: Any, patient: Any) -> None:
        """Test GET request when no best appointments exist"""
        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["best_appointments"]) == 0

    @pytest.mark.django_db
    def test_get_best_appointments_excludes_not_interested(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test GET request excludes appointments marked as not interested"""
        # Mark the appointment as not interested
        best_appointment_found.not_interested = True
        best_appointment_found.save()

        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": best_appointment_found.patient.id})

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True
        assert len(data["best_appointments"]) == 0  # Should be excluded

    @pytest.mark.django_db
    def test_get_best_appointments_includes_interested_and_excludes_not_interested(
        self, client: Any, find_appointment: Any, patient: Any
    ) -> None:
        """Test GET request includes interested appointments and excludes not interested ones"""
        # Create two appointments - one interested, one not interested
        interested_appointment = BestAppointmentFound.objects.create(
            appointment_wanted=find_appointment,
            patient=patient,
            datetime=timezone.now() + timedelta(days=1),
            not_interested=False,
        )

        not_interested_appointment = BestAppointmentFound.objects.create(
            appointment_wanted=find_appointment,
            patient=patient,
            datetime=timezone.now() + timedelta(days=2),
            not_interested=True,
        )

        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": patient.id})

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert len(response_data["best_appointments"]) == 1  # Only the interested one

        # Verify it's the interested appointment
        returned_appointment = response_data["best_appointments"][0]
        assert returned_appointment["id"] == interested_appointment.id

    @pytest.mark.django_db
    def test_get_filters_appointments_in_the_past(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test GET request filters appointments in the past"""
        # Set the datetime to the past
        best_appointment_found.datetime = timezone.now() - timedelta(days=1)
        best_appointment_found.save()

        url = reverse("sanatorio_allende:api_best_appointments")
        response = client.get(url, {"patient_id": best_appointment_found.patient.id})

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert len(response_data["best_appointments"]) == 0

    @pytest.mark.django_db
    def test_patch_mark_appointment_not_interested_success(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test successful PATCH request to mark appointment as not interested"""
        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "appointment_id": best_appointment_found.id,
            "not_interested": True,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Appointment marked as not interested" in response_data["message"]

        # Verify the appointment was actually updated
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.not_interested is True

    @pytest.mark.django_db
    def test_patch_mark_appointment_interested_success(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test successful PATCH request to mark appointment as interested"""
        # First mark as not interested
        best_appointment_found.not_interested = True
        best_appointment_found.save()

        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "appointment_id": best_appointment_found.id,
            "not_interested": False,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Appointment marked as interested" in response_data["message"]

        # Verify the appointment was actually updated
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.not_interested is False

    @pytest.mark.django_db
    def test_patch_mark_appointment_not_interested_default_value(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test PATCH request with default not_interested value (True)"""
        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "appointment_id": best_appointment_found.id,
            # not_interested not provided, should default to True
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Appointment marked as not interested" in response_data["message"]

        # Verify the appointment was actually updated
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.not_interested is True

    @pytest.mark.django_db
    def test_patch_mark_appointment_missing_appointment_id(self, client: Any) -> None:
        """Test PATCH request without appointment_id parameter"""
        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "not_interested": True,
            # appointment_id missing
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert "appointment_id is required" in str(data["error"])

    @pytest.mark.django_db
    def test_patch_mark_appointment_not_found(self, client: Any) -> None:
        """Test PATCH request with non-existent appointment_id"""
        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "appointment_id": 999,
            "not_interested": True,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Appointment not found" in str(data["error"])

    @pytest.mark.django_db
    def test_patch_mark_appointment_for_other_user(
        self, evil_client: Any, best_appointment_found: Any
    ) -> None:
        """Test PATCH request for appointment belonging to another user"""
        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "appointment_id": best_appointment_found.id,
            "not_interested": True,
        }
        response = evil_client.patch(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Appointment does not belong to the current user" in data["error"]

        # Verify the appointment was not changed
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.not_interested is False

    @pytest.mark.django_db
    def test_patch_mark_appointment_with_patient_no_user(
        self, client: Any, find_appointment: Any, patient: Any
    ) -> None:
        """Test PATCH request for appointment with patient that has no user"""
        # Create a patient without a user
        patient.user = None
        patient.save()

        best_appointment = BestAppointmentFound.objects.create(
            appointment_wanted=find_appointment,
            patient=patient,
            datetime=timezone.now(),
        )

        url = reverse("sanatorio_allende:api_best_appointments")
        data = {
            "appointment_id": best_appointment.id,
            "not_interested": True,
        }
        response = client.patch(url, json.dumps(data), content_type="application/json")

        # Should return 401 since patient has no user
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert (
            "Appointment does not belong to the current user" in response_data["error"]
        )


class TestPatientListView:
    """Test cases for PatientListView"""

    @pytest.mark.django_db
    def test_get_patients_success(self, client: Any, patient: Any) -> None:
        """Test successful GET request to list patients"""
        url = reverse("sanatorio_allende:api_patients")
        response = client.get(url)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert len(response_data["patients"]) == 1
        assert response_data["patients"][0]["name"] == patient.name
        assert response_data["patients"][0]["id_paciente"] == patient.id_paciente
        assert response_data["patients"][0]["docid"] == patient.docid
        assert "updated_at" in response_data["patients"][0]

    @pytest.mark.django_db
    def test_get_patients_empty(self, client: Any) -> None:
        """Test GET request when no patients exist"""
        url = reverse("sanatorio_allende:api_patients")
        response = client.get(url)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert len(response_data["patients"]) == 0

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_post_create_patient_success(self, mock_post: Any, client: Any) -> None:
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
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Patient created successfully" in response_data["message"]
        assert "patient_id" in response_data

        created_patient = PacienteAllende.objects.get(id=response_data["patient_id"])
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
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_post_create_patient_invalid_credentials(
        self, mock_post: Any, client: Any
    ) -> None:
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
    def test_post_create_patient_missing_parameters(self, client: Any) -> None:
        """Test POST request with missing parameters"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"name": "Test Patient"}  # Missing docid and password
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert "name, docid, and password are required" in response_data["error"]

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_post_create_patient_already_exists(
        self, mock_post: Any, client: Any, patient: Any
    ) -> None:
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
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert "Patient already exists with this document ID" in response_data["error"]

    @pytest.mark.django_db
    def test_delete_patient_success(self, client: Any, patient: Any) -> None:
        """Test successful DELETE request to delete patient"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"patient_id": patient.id}
        response = client.delete(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Patient deleted successfully" in response_data["message"]

        # Verify the patient was actually deleted
        with pytest.raises(PacienteAllende.DoesNotExist):
            PacienteAllende.objects.get(id=patient.id)

    @pytest.mark.django_db
    def test_delete_patient_missing_patient_id(self, client: Any) -> None:
        """Test DELETE request without patient_id parameter"""
        url = reverse("sanatorio_allende:api_patients")
        data: dict = {}  # Missing patient_id
        response = client.delete(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert "patient_id is required" in response_data["error"]

    @pytest.mark.django_db
    def test_delete_patient_not_found(self, client: Any) -> None:
        """Test DELETE request with non-existent patient_id"""
        url = reverse("sanatorio_allende:api_patients")
        data = {"patient_id": 999}
        response = client.delete(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert "Patient not found" in response_data["error"]

    @pytest.mark.django_db
    def test_delete_patient_for_other_user(
        self, evil_client: Any, patient: Any
    ) -> None:
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
    def test_post_register_device_new(self, client: Any) -> None:
        """Test successful POST request to register new device"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {
            "push_token": "new_push_token_123",
            "platform": "expo",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Device registered successfully" in response_data["message"]
        assert response_data["created"] is True

    @pytest.mark.django_db
    def test_post_register_device_existing(
        self, client: Any, device_registration: Any
    ) -> None:
        """Test POST request to update existing device"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {
            "push_token": device_registration.push_token,
            "platform": "ios",
        }
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert "Device registered successfully" in response_data["message"]
        assert response_data["created"] is False

        # Verify the device was updated
        device_registration.refresh_from_db()
        assert device_registration.platform == "ios"
        assert device_registration.is_active is True

    @pytest.mark.django_db
    def test_post_register_device_missing_token(self, client: Any) -> None:
        """Test POST request without push_token"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {"platform": "expo"}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert "push_token is required" in response_data["error"]

    @pytest.mark.django_db
    def test_post_register_device_default_platform(self, client: Any) -> None:
        """Test POST request with default platform"""
        url = reverse("sanatorio_allende:api_register_device")
        data = {"push_token": "test_token_123"}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True

        # Verify default platform was used
        device = DeviceRegistration.objects.get(push_token="test_token_123")
        assert device.platform == "expo"


class TestConfirmAppointmentView:
    """Test cases for ConfirmAppointmentView"""

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_post_confirm_appointment_success(
        self, mock_post: Any, client: Any, best_appointment_found: Any
    ) -> None:
        """Test successful POST request to confirm an appointment"""
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: {"Entidad": {"Id": TEST_CONFIRMED_ID_TURNO}},
            },
        )()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_confirm_appointment")
        data = {"appointment_id": best_appointment_found.id}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["success"] is True
        assert response_data["message"] == "Appointment confirmed successfully"

        # Verify the appointment was marked as confirmed
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.confirmed is True
        assert best_appointment_found.confirmed_at is not None
        assert best_appointment_found.confirmed_id_turno == TEST_CONFIRMED_ID_TURNO

        # Verify the correct data was sent to the Allende API
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert (
            call_args[0][0]
            == "https://miportal.sanatorioallende.com/backend/api/turnos/Asignar"
        )
        assert (
            call_args[1]["headers"]["authorization"]
            == best_appointment_found.patient.token
        )

    @pytest.mark.django_db
    def test_post_confirm_appointment_invalid_json(self, client: Any) -> None:
        """Test POST request with invalid JSON"""
        url = reverse("sanatorio_allende:api_confirm_appointment")
        response = client.post(url, "invalid json", content_type="application/json")

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["success"] is False
        assert response_data["error"] == "Invalid JSON"

    @pytest.mark.django_db
    def test_post_confirm_appointment_not_found(self, client: Any) -> None:
        """Test POST request with non-existent appointment_id"""
        url = reverse("sanatorio_allende:api_confirm_appointment")
        data = {"appointment_id": 999}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_post_confirm_appointment_already_confirmed(
        self, client: Any, best_appointment_found: Any
    ) -> None:
        """Test POST request for an appointment that is already confirmed"""
        # Mark the appointment as already confirmed
        best_appointment_found.confirmed = True
        best_appointment_found.confirmed_at = timezone.now()
        best_appointment_found.save()

        url = reverse("sanatorio_allende:api_confirm_appointment")
        data = {"appointment_id": best_appointment_found.id}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["success"] is False
        assert data["error"] == "Appointment is already confirmed"

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_post_confirm_appointment_unauthorized(
        self, mock_post: Any, client: Any, best_appointment_found: Any
    ) -> None:
        """Test POST request when the Allende API returns unauthorized"""
        # Mock the unauthorized response from the Allende API
        from sanatorio_allende.allende_api import UnauthorizedException

        mock_post.side_effect = UnauthorizedException()

        url = reverse("sanatorio_allende:api_confirm_appointment")
        data = {"appointment_id": best_appointment_found.id}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["success"] is False
        assert data["error"] == "Unauthorized - please re-authenticate"

        # Verify the appointment was not marked as confirmed
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.confirmed is False
        assert best_appointment_found.confirmed_at is None

    @pytest.mark.django_db
    def test_post_confirm_appointment_for_other_user(
        self, evil_client: Any, best_appointment_found: Any
    ) -> None:
        """Test POST request for an appointment belonging to another user"""
        url = reverse("sanatorio_allende:api_confirm_appointment")
        data = {"appointment_id": best_appointment_found.id}
        response = evil_client.post(
            url, json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 401

    @pytest.mark.django_db
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_post_confirm_appointment_verify_appointment_data_structure(
        self, mock_post: Any, client: Any, best_appointment_found: Any
    ) -> None:
        """Test that the appointment data structure sent to Allende API is correct"""
        # Mock the successful response from the Allende API
        mock_response = type(
            "MockResponse",
            (),
            {
                "status_code": 200,
                "json": lambda self: {"Entidad": {"Id": TEST_CONFIRMED_ID_TURNO}},
            },
        )()
        mock_post.return_value = mock_response

        url = reverse("sanatorio_allende:api_confirm_appointment")
        data = {"appointment_id": best_appointment_found.id}
        response = client.post(url, json.dumps(data), content_type="application/json")

        assert response.status_code == 200

        # Verify the appointment data structure sent to Allende API
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        appointment_data = call_args[1]["json"]

        assert appointment_data == {
            "CriterioBusquedaDto": {
                "IdPaciente": TEST_PATIENT_ID,
                "IdServicio": TEST_SERVICIO_ID,
                "IdSucursal": TEST_SUCURSAL_ID,
                "IdRecurso": TEST_RECURSO_ID,
                "IdEspecialidad": TEST_ESPECIALIDAD_ID,
                "ControlarEdad": False,
                "IdTipoDeTurno": TEST_TIPO_TURNO_ID,
                "IdFinanciador": TEST_FINANCIADOR_ID,
                "IdTipoRecurso": TEST_TIPO_RECURSO_ID,
                "IdPlan": TEST_PLAN_ID,
                "Prestaciones": [
                    {
                        "IdPrestacion": TEST_PRESTACION_ID,
                        "IdItemSolicitudEstudios": 0,
                    }
                ],
            },
            "TurnoElegidoDto": {
                "Fecha": best_appointment_found.datetime.strftime("%Y-%m-%dT00:00:00"),
                "Hora": (best_appointment_found.datetime - timedelta(hours=3)).strftime(
                    "%H:%M"
                ),
                "IdItemDePlantilla": TEST_ITEM_PLANTILLA_ID,
                "IdPlantillaTurno": TEST_PLANTILLA_TURNO_ID,
                "IdSucursal": TEST_SUCURSAL_ID,
                "DuracionIndividual": TEST_DURACION_INDIVIDUAL,
                "RequisitoAdministrativoAlOtorgar": "DNI\nCredencial Financiador\n AUTORIZACION: Con autorización online",
            },
            "Observaciones": None,
        }
