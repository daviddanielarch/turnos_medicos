import json
from typing import Any
from unittest.mock import patch

import pytest
from conftest import (
    TEST_CONFIRMED_ID_TURNO,
    TEST_ESPECIALIDAD_ID,
    TEST_FINANCIADOR_ID,
    TEST_FRESH_ALLENDE_TOKEN,
    TEST_PATIENT_ID,
    TEST_PLAN_ID,
    TEST_SERVICIO_ID,
    TEST_SUCURSAL_ID,
    FakeAllende,
)
from django.urls import reverse
from django.utils import timezone

from sanatorio_allende.models import BestAppointmentFound, PacienteAllende
from sanatorio_allende.services.auth import LOGIN_ATTEMPTS, AllendeAuthService


@pytest.mark.django_db
class TestExpiredAllendeToken:
    """
    The patient's stored Allende token expires on its own schedule, so every
    request that reaches Allende has to survive finding it expired.
    """

    def test_doctor_search_logs_in_again(
        self, client: Any, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url, {"patient_id": patient.id, "pattern": "gobelet"})

        assert response.status_code == 200
        doctors = json.loads(response.content)["doctors"]["Profesionales"]
        assert [doctor["Nombre"] for doctor in doctors] == ["GOBELET JAQUELINA MARICEL"]

    def test_fresh_token_is_kept_for_the_next_request(
        self, client: Any, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
        url = reverse("sanatorio_allende:api_doctors")
        client.get(url, {"patient_id": patient.id, "pattern": "gobelet"})
        client.get(url, {"patient_id": patient.id, "pattern": "gobelet"})

        patient.refresh_from_db()
        assert patient.token == TEST_FRESH_ALLENDE_TOKEN
        assert fake_allende.login_count == 1

    def test_valid_token_does_not_log_in(
        self, client: Any, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
        fake_allende.valid_token = patient.token or ""

        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url, {"patient_id": patient.id, "pattern": "gobelet"})

        assert response.status_code == 200
        assert fake_allende.login_count == 0

    def test_doctor_search_is_unauthorized_when_login_is_rejected(
        self, client: Any, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
        """A patient whose Allende password changed cannot be logged in again"""
        fake_allende.password = "changed-in-the-portal"

        url = reverse("sanatorio_allende:api_doctors")
        response = client.get(url, {"patient_id": patient.id, "pattern": "gobelet"})

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["success"] is False
        assert data["error"] == "Unauthorized - please re-authenticate"
        assert fake_allende.login_count == 1

    def test_appointment_types_log_in_again(
        self, client: Any, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
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
        appointment_types = json.loads(response.content)["appointment_types"]
        assert [item["Nombre"] for item in appointment_types] == ["CONSULTA"]

    def test_confirming_an_appointment_logs_in_again(
        self,
        client: Any,
        best_appointment_found: BestAppointmentFound,
        fake_allende: FakeAllende,
    ) -> None:
        url = reverse("sanatorio_allende:api_appointment")
        body = json.dumps({"appointment_id": best_appointment_found.id})
        response = client.post(url, body, content_type="application/json")

        assert response.status_code == 200
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.confirmed is True
        assert best_appointment_found.confirmed_id_turno == TEST_CONFIRMED_ID_TURNO

    def test_cancelling_an_appointment_logs_in_again(
        self,
        client: Any,
        best_appointment_found: BestAppointmentFound,
        fake_allende: FakeAllende,
    ) -> None:
        best_appointment_found.confirmed = True
        best_appointment_found.confirmed_at = timezone.now()
        best_appointment_found.confirmed_id_turno = TEST_CONFIRMED_ID_TURNO
        best_appointment_found.save()

        url = reverse("sanatorio_allende:api_appointment")
        body = json.dumps({"appointment_id": best_appointment_found.id})
        response = client.delete(url, body, content_type="application/json")

        assert response.status_code == 200
        best_appointment_found.refresh_from_db()
        assert best_appointment_found.confirmed is False


@pytest.mark.django_db
class TestBackgroundLogin:
    """The login the appointment search job runs before each patient"""

    def test_login_stores_token_and_patient_data(
        self, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
        patient.id_financiador = None
        patient.id_plan = None
        patient.save()

        assert AllendeAuthService(patient).login() == TEST_FRESH_ALLENDE_TOKEN

        patient.refresh_from_db()
        assert patient.token == TEST_FRESH_ALLENDE_TOKEN
        assert patient.id_paciente == str(TEST_PATIENT_ID)
        assert patient.id_financiador == TEST_FINANCIADOR_ID
        assert patient.id_plan == TEST_PLAN_ID

    @patch("sanatorio_allende.services.auth.time.sleep")
    def test_login_gives_up_after_retrying(
        self, mock_sleep: Any, patient: PacienteAllende, fake_allende: FakeAllende
    ) -> None:
        fake_allende.password = "changed-in-the-portal"

        with pytest.raises(Exception, match="Check username or password"):
            AllendeAuthService(patient).login()

        assert fake_allende.login_count == LOGIN_ATTEMPTS
        assert [call.args[0] for call in mock_sleep.call_args_list] == [2, 4]
