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
        appointment_wanted=find_appointment, patient=patient, datetime=timezone.now()
    )


@pytest.fixture
def device_registration(user):
    """Create a test device registration"""
    return DeviceRegistration.objects.create(
        user=user, push_token="test_push_token_123", platform="expo", is_active=True
    )
