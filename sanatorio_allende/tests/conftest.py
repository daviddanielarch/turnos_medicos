import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from sanatorio_allende.models import (
    AppointmentType,
    BestAppointmentFound,
    DeviceRegistration,
    Doctor,
    Especialidad,
    FindAppointment,
    PacienteAllende,
)

# Test constants to replace hardcoded values
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
TEST_ITEM_SOLICITUD_ESTUDIOS_ID = 0
TEST_DURACION_INDIVIDUAL = 20
TEST_ITEM_PLANTILLA_ID = 12
TEST_PLANTILLA_TURNO_ID = 10
TEST_CONFIRMED_ID_TURNO = 100


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
    """Create a test user for testing unauthorized access"""
    return User.objects.create_user(
        username="eviluser", email="evil@example.com", password="evilpass123"
    )


@pytest.fixture
def evil_client(evil_user):
    """Django test client fixture with evil user for testing unauthorized access"""
    client = Client()
    client.force_login(evil_user)
    return client


@pytest.fixture
def especialidad():
    """Create a test especialidad"""
    return Especialidad.objects.create(
        name="Cardiología",
        id_especialidad=TEST_ESPECIALIDAD_ID,
        id_servicio=TEST_SERVICIO_ID,
        id_sucursal=TEST_SUCURSAL_ID,
        sucursal="Centro",
        servicio="Cardiología",
    )


@pytest.fixture
def doctor(especialidad):
    """Create a test doctor"""
    return Doctor.objects.create(
        name="Dr. Juan Pérez",
        id_recurso=TEST_RECURSO_ID,
        id_tipo_recurso=TEST_TIPO_RECURSO_ID,
        especialidad=especialidad,
    )


@pytest.fixture
def appointment_type(especialidad):
    """Create a test appointment type"""
    return AppointmentType.objects.create(
        name="CONSULTA",
        id_tipo_turno=TEST_PRESTACION_ID,
        especialidad=especialidad,
        id_tipo_prestacion=TEST_TIPO_TURNO_ID,
    )


@pytest.fixture
def patient(user):
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
def find_appointment(doctor, appointment_type, patient):
    """Create a test find appointment"""
    return FindAppointment.objects.create(
        doctor=doctor,
        tipo_de_turno=appointment_type,
        patient=patient,
        desired_timeframe="2 weeks",
        active=True,
    )


@pytest.fixture
def best_appointment_found(find_appointment, patient):
    """Create a test best appointment found"""
    return BestAppointmentFound.objects.create(
        appointment_wanted=find_appointment,
        patient=patient,
        datetime=timezone.now(),
        duracion_individual=TEST_DURACION_INDIVIDUAL,
        id_plantilla_turno=TEST_PLANTILLA_TURNO_ID,
        id_item_plantilla=TEST_ITEM_PLANTILLA_ID,
        hora="23:03",
    )


@pytest.fixture
def device_registration(user):
    """Create a test device registration"""
    return DeviceRegistration.objects.create(
        user=user, push_token="test_push_token_123", platform="expo", is_active=True
    )
