import json
from typing import Any, Dict, Iterator, List
from unittest.mock import patch

import pytest
import sentry_sdk
from conftest import (
    TEST_ESPECIALIDAD_ID,
    TEST_FINANCIADOR_ID,
    TEST_PATIENT_ID,
    TEST_PLAN_ID,
    TEST_PRESTACION_ID,
    TEST_RECURSO_ID,
    TEST_SERVICIO_ID,
    TEST_SUCURSAL_ID,
    TEST_TIPO_RECURSO_ID,
)
from django.conf import settings
from django.core.management import call_command
from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport

from sanatorio_allende.management.commands.find_appointments import (
    ALLENDE_CLIENT_SYSTEM_ID,
)

RAILWAY_CRON_CONFIG = settings.BASE_DIR / "terraform" / "configs" / "buscar_turnos.json"


class CheckInRecorder(Transport):
    """Stands in for Sentry's ingestion endpoint and keeps the cron check-ins"""

    def __init__(self) -> None:
        super().__init__()
        self.check_ins: List[Dict[str, Any]] = []

    def capture_envelope(self, envelope: Envelope) -> None:
        for item in envelope.items:
            check_in = item.payload.json
            if item.type == "check_in" and check_in is not None:
                self.check_ins.append(check_in)


@pytest.fixture
def sentry_check_ins() -> Iterator[List[Dict[str, Any]]]:
    """The check-ins the code under test sends to Sentry, in order"""
    recorder = CheckInRecorder()
    client = sentry_sdk.Client(
        dsn="https://public@sentry.invalid/1", transport=recorder
    )
    with sentry_sdk.isolation_scope() as scope:
        scope.set_client(client)
        yield recorder.check_ins


class TestFindAppointmentsCommand:
    """Test the payload the command sends to Allende"""

    @pytest.mark.django_db
    @patch("sanatorio_allende.management.commands.find_appointments.Allende")
    @patch("sanatorio_allende.management.commands.find_appointments.AllendeAuthService")
    def test_search_payload_includes_client_system_id(
        self,
        mock_auth_service: Any,
        mock_allende: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
    ) -> None:
        """
        Allende answers 200 with an empty result set when IdSistemaCliente is
        missing, so an absent field looks exactly like "no appointments" and the
        search goes blind. Pin the field down.
        """
        mock_allende.return_value.search_best_date_appointment.return_value = None

        call_command("find_appointments")

        mock_allende.return_value.search_best_date_appointment.assert_called_once()
        doctor_data = mock_allende.return_value.search_best_date_appointment.call_args[
            0
        ][0]
        assert doctor_data["IdSistemaCliente"] == ALLENDE_CLIENT_SYSTEM_ID

    @pytest.mark.django_db
    @patch("sanatorio_allende.management.commands.find_appointments.Allende")
    @patch("sanatorio_allende.management.commands.find_appointments.AllendeAuthService")
    def test_search_payload_carries_patient_and_appointment_ids(
        self,
        mock_auth_service: Any,
        mock_allende: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
    ) -> None:
        """Test that the rest of the search criteria reach Allende unchanged"""
        mock_allende.return_value.search_best_date_appointment.return_value = None

        call_command("find_appointments")

        doctor_data = mock_allende.return_value.search_best_date_appointment.call_args[
            0
        ][0]
        assert doctor_data == {
            "IdPaciente": TEST_PATIENT_ID,
            "IdServicio": TEST_SERVICIO_ID,
            "IdSucursal": TEST_SUCURSAL_ID,
            "IdRecurso": TEST_RECURSO_ID,
            "IdEspecialidad": TEST_ESPECIALIDAD_ID,
            "IdTipoRecurso": TEST_TIPO_RECURSO_ID,
            "ControlarEdad": False,
            "IdSistemaCliente": ALLENDE_CLIENT_SYSTEM_ID,
            "IdFinanciador": TEST_FINANCIADOR_ID,
            "IdPlan": TEST_PLAN_ID,
            "Prestaciones": [
                {
                    "IdPrestacion": TEST_PRESTACION_ID,
                    "IdItemSolicitudEstudios": 0,
                }
            ],
        }

    @pytest.mark.django_db
    @patch("sanatorio_allende.management.commands.find_appointments.Allende")
    @patch("sanatorio_allende.management.commands.find_appointments.AllendeAuthService")
    def test_inactive_appointments_are_not_searched(
        self,
        mock_auth_service: Any,
        mock_allende: Any,
        find_appointment: Any,
        patient: Any,
        user: Any,
    ) -> None:
        """Test that deactivated searches are left alone"""
        find_appointment.active = False
        find_appointment.save(update_fields=["active"])

        call_command("find_appointments")

        mock_allende.return_value.search_best_date_appointment.assert_not_called()


class TestFindAppointmentsMonitor:
    """
    Sentry alerts when the scheduled search stops checking in, which is the only
    signal that the job is no longer running at all.
    """

    @pytest.mark.django_db
    def test_run_checks_in_when_it_starts_and_when_it_finishes(
        self, sentry_check_ins: List[Dict[str, Any]]
    ) -> None:
        call_command("find_appointments")

        assert [check_in["status"] for check_in in sentry_check_ins] == [
            "in_progress",
            "ok",
        ]
        started, finished = sentry_check_ins
        assert started["monitor_slug"] == "buscar-turnos"
        assert finished["monitor_slug"] == "buscar-turnos"
        assert finished["check_in_id"] == started["check_in_id"]

    @pytest.mark.django_db
    @patch("sanatorio_allende.management.commands.find_appointments.Allende")
    @patch("sanatorio_allende.management.commands.find_appointments.AllendeAuthService")
    def test_run_that_crashes_checks_in_as_failed(
        self,
        mock_auth_service: Any,
        mock_allende: Any,
        sentry_check_ins: List[Dict[str, Any]],
        find_appointment: Any,
        patient: Any,
        user: Any,
    ) -> None:
        mock_allende.return_value.search_best_date_appointment.side_effect = (
            RuntimeError("Allende is down")
        )

        with pytest.raises(RuntimeError, match="Allende is down"):
            call_command("find_appointments")

        assert [check_in["status"] for check_in in sentry_check_ins] == [
            "in_progress",
            "error",
        ]

    @pytest.mark.django_db
    def test_monitor_expects_the_schedule_railway_runs_the_job_on(
        self, sentry_check_ins: List[Dict[str, Any]]
    ) -> None:
        """
        Sentry decides a run was missed from the schedule the job reports, so a
        schedule that drifts from the real one means false or missing alerts.
        """
        railway_schedule = json.loads(RAILWAY_CRON_CONFIG.read_text())["deploy"][
            "cronSchedule"
        ]

        call_command("find_appointments")

        assert sentry_check_ins[0]["monitor_config"]["schedule"] == {
            "type": "crontab",
            "value": railway_schedule,
        }
