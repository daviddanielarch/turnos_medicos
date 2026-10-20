from typing import Any
from unittest.mock import patch

import pytest
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
from django.core.management import call_command

from sanatorio_allende.management.commands.find_appointments import (
    ALLENDE_CLIENT_SYSTEM_ID,
)


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
