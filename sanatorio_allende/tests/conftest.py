from datetime import timedelta

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
        password="testpass123",
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
