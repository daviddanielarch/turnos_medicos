import base64
from datetime import timedelta
from typing import Any, Iterator, Optional
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from sanatorio_allende.models import (
    BestAppointmentFound,
    DeviceRegistration,
    FindAppointment,
    PacienteAllende,
)

TEST_PATIENT_ID = 12345
TEST_SERVICIO_ID = 7
TEST_SUCURSAL_ID = 2
TEST_RECURSO_ID = 1
TEST_ESPECIALIDAD_ID = 19
TEST_TIPO_TURNO_ID = 1
TEST_FINANCIADOR_ID = 12345
TEST_TIPO_RECURSO_ID = 12
TEST_PLAN_ID = 6
TEST_PRESTACION_ID = 5495
TEST_TIPO_PRESTACION_ID = 1
TEST_DURACION_INDIVIDUAL = 20
TEST_ITEM_PLANTILLA_ID = 12
TEST_PLANTILLA_TURNO_ID = 10
TEST_CONFIRMED_ID_TURNO = 100
TEST_ID_PLANTILLA_TURNO = 81268
TEST_ID_ITEM_PLANTILLA = 767071
TEST_PATIENT_PASSWORD = "testpass123"
TEST_FRESH_ALLENDE_TOKEN = "Bearer fresh-token"


@pytest.fixture
def user() -> User:
    """Create a test user"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def client(user: User) -> Client:
    """Django test client fixture with authenticated user"""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def evil_user() -> User:
    """Create a test user for testing unauthorized access"""
    return User.objects.create_user(
        username="eviluser", email="evil@example.com", password="evilpass123"
    )


@pytest.fixture
def evil_client(evil_user: User) -> Client:
    """Django test client fixture with evil user for testing unauthorized access"""
    client = Client()
    client.force_login(evil_user)
    return client


@pytest.fixture
def patient(user: User) -> PacienteAllende:
    """Create a test patient"""
    return PacienteAllende.objects.create(
        user=user,
        name="Juan Pérez",
        id_paciente=str(TEST_PATIENT_ID),
        docid="12345678",
        password=TEST_PATIENT_PASSWORD,
        token="test_auth_token_123",
        id_financiador=TEST_FINANCIADOR_ID,
        id_plan=TEST_PLAN_ID,
    )


@pytest.fixture
def find_appointment(patient: PacienteAllende) -> FindAppointment:
    """Create a test find appointment"""
    return FindAppointment.objects.create(
        doctor_name="Dr. Juan Pérez",
        id_servicio=TEST_SERVICIO_ID,
        servicio="Cardiología",
        id_sucursal=TEST_SUCURSAL_ID,
        sucursal="Centro",
        id_especialidad=TEST_ESPECIALIDAD_ID,
        especialidad="Cardiología",
        id_recurso=TEST_RECURSO_ID,
        id_tipo_recurso=TEST_TIPO_RECURSO_ID,
        id_prestacion=TEST_PRESTACION_ID,
        id_tipo_prestacion=TEST_TIPO_PRESTACION_ID,
        nombre_tipo_prestacion="CONSULTA",
        patient=patient,
        desired_timeframe="2 weeks",
        active=True,
    )


@pytest.fixture
def best_appointment_found(
    find_appointment: FindAppointment, patient: PacienteAllende
) -> BestAppointmentFound:
    """Create a test best appointment found"""
    return BestAppointmentFound.objects.create(
        appointment_wanted=find_appointment,
        patient=patient,
        datetime=timezone.now() + timedelta(days=1),
        duracion_individual=TEST_DURACION_INDIVIDUAL,
        id_plantilla_turno=TEST_PLANTILLA_TURNO_ID,
        id_item_plantilla=TEST_ITEM_PLANTILLA_ID,
    )


@pytest.fixture
def device_registration(user: User) -> DeviceRegistration:
    """Create a test device registration"""
    return DeviceRegistration.objects.create(
        user=user, push_token="test_push_token_123", platform="expo", is_active=True
    )


class FakeAllende:
    """
    Stands in for the Allende HTTP API. It only accepts `valid_token`, and hands
    that token out to whoever logs in with `password`, so a patient whose stored
    token differs from `valid_token` is a patient with an expired token.
    """

    def __init__(self) -> None:
        self.valid_token = TEST_FRESH_ALLENDE_TOKEN
        self.password = TEST_PATIENT_PASSWORD
        self.login_count = 0

    @staticmethod
    def _response(status_code: int, payload: Any = None) -> MagicMock:
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = payload
        return response

    def _is_authorized(self, headers: Optional[dict]) -> bool:
        return (headers or {}).get("authorization") == self.valid_token

    def post(
        self,
        url: str,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        **kwargs: Any,
    ) -> MagicMock:
        if url.endswith("/backend/Token"):
            self.login_count += 1
            password = base64.b64decode((json or {})["Password"]).decode("utf-8")
            if password != self.password:
                return self._response(400, {"Error": "invalid_grant"})
            access_token = self.valid_token.replace("Bearer ", "")
            return self._response(200, {"Access_token": access_token, "Error": ""})

        if not self._is_authorized(headers):
            return self._response(401)
        if "ObtenerEspecialidadServicioProfesionalPorCriterio" in url:
            return self._response(
                200,
                {
                    "Especialidades": [],
                    "Profesionales": [{"Nombre": "GOBELET JAQUELINA MARICEL"}],
                },
            )
        if url.endswith("turnos/Asignar"):
            return self._response(200, {"Entidad": {"Id": TEST_CONFIRMED_ID_TURNO}})
        if url.endswith("turnos/CancelarTurno"):
            return self._response(200, {"IsOk": True, "Message": ""})
        raise AssertionError(f"Unexpected POST to {url}")

    def get(self, url: str, headers: Optional[dict] = None, **kwargs: Any) -> MagicMock:
        if not self._is_authorized(headers):
            return self._response(401)
        if "GetInfoSeguridadCurrentUser" in url:
            return self._response(200, {"IdPaciente": TEST_PATIENT_ID})
        if "Paciente/ObtenerPorId" in url:
            return self._response(
                200,
                {
                    "CoberturaPorDefecto": {
                        "IdMutual": TEST_FINANCIADOR_ID,
                        "IdPlanMutual": TEST_PLAN_ID,
                    }
                },
            )
        if "PrestacionMedica" in url:
            return self._response(
                200, [{"Id": TEST_PRESTACION_ID, "Nombre": "CONSULTA"}]
            )
        return self._response(200, {})


@pytest.fixture
def fake_allende() -> Iterator[FakeAllende]:
    """Replace the Allende HTTP API with a fake that rejects the patient's stored token"""
    fake = FakeAllende()
    with patch(
        "sanatorio_allende.allende_api.requests.post", side_effect=fake.post
    ), patch("sanatorio_allende.allende_api.requests.get", side_effect=fake.get):
        yield fake
