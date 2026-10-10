#!/usr/bin/env python3

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401

TOKEN_URL = "https://miportal.sanatorioallende.com/backend/Token"
API_URL = "https://miportal.sanatorioallende.com/backend/api/"
# Public OAuth client credentials of the patient portal (embedded in its web bundle)
PORTAL_CLIENT_AUTHORIZATION = "Basic " + base64.b64encode(
    b"AppSA:7SeGvoNkZze03n6L"
).decode("utf-8")


class UnauthorizedException(Exception):
    pass


@dataclass
class CancelAppointmentResponse:
    IsOk: bool
    Message: str
    HasWarnings: bool
    WarningMessage: str
    IdEntidadValidada: int


@dataclass
class UserData:
    id_financiador: str
    id_plan: str


@dataclass
class BookAppointmentResponse:
    id_turno: Optional[int]
    data: Optional[dict]


logger = logging.getLogger(__name__)


class Allende:
    def __init__(self, auth_header: Optional[str] = None):
        self.auth_header = auth_header
        self.user_id: Optional[str] = None

    def get_user_id(self) -> Optional[str]:
        return self.user_id

    def get_auth_header(self) -> Optional[str]:
        return self.auth_header

    @staticmethod
    def _b64(value: str) -> str:
        return base64.b64encode(value.encode("utf-8")).decode("utf-8")

    @classmethod
    def _request_access_token(cls, dni: str, password: str) -> Optional[str]:
        """Log in the same way the patient portal does and return the access token"""
        response = requests.post(
            TOKEN_URL,
            headers={"Authorization": PORTAL_CLIENT_AUTHORIZATION},
            json={
                "IdTipoDocumento": 1,
                "NumeroDocumento": cls._b64(dni),
                "Password": cls._b64(password),
                "Sistema": cls._b64("app-portal-paciente"),
                "Grant_type": "password",
                "Id": 0,
                "ChangePassword": False,
                "IsAnonymous": False,
                "SolicitarReCaptcha": False,
                "ReCaptcha": "",
            },
        )
        if response.status_code != HTTP_OK:
            return None

        data = response.json()
        if data.get("Error"):
            return None
        access_token: Optional[str] = data.get("Access_token")
        return access_token

    @classmethod
    def validate_credentials(cls, dni: str, password: str) -> bool:
        return cls._request_access_token(dni, password) is not None

    def login(self, user: str, password: str) -> str:
        if self.auth_header and self.is_authorized(self.auth_header):
            return self.auth_header

        access_token = self._request_access_token(user, password)
        if not access_token:
            raise Exception("Check username or password")
        self.auth_header = f"Bearer {access_token}"

        response = requests.get(
            f"{API_URL}Usuario/GetInfoSeguridadCurrentUser/",
            headers={"authorization": self.auth_header},
        )
        response.raise_for_status()
        user_id = response.json().get("IdPaciente")
        if not user_id:
            raise Exception("Could not get user id")
        self.user_id = str(user_id)

        return self.auth_header

    def get_doctors(self, pattern: str) -> List[dict]:
        """
        Response format:
                {
            "Especialidades": [],
            "Profesionales": [
                {
                    "IdRecurso": 25643,
                    "IdTipoRecurso": 1,
                    "NumeroMatricula": 25643,
                    "Nombre": "GOBELET JAQUELINA MARICEL",
                    "IdEspecialidad": 7,
                    "Especialidad": "GASTROENTEROLOGIA",
                    "IdServicio": 13,
                    "Servicio": "GASTROENTEROLOGIA",
                    "IdSucursal": 2,
                    "Sucursal": "CERRO"
                }
            ]
        }
        """
        response = requests.post(
            "https://miportal.sanatorioallende.com/backend/api/TurnosBuscadorGenerico/ObtenerEspecialidadServicioProfesionalPorCriterio",
            headers={"authorization": self.auth_header},
            json={
                "Criterio": pattern,
            },
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        return response.json()  # type: ignore

    def get_user_data(self) -> UserData:
        if not self.user_id:
            raise Exception("User id not found")

        response = requests.get(
            f"https://miportal.sanatorioallende.com/backend/api/Paciente/ObtenerPorId/{self.user_id}",
            headers={"authorization": self.auth_header},
        )
        data = response.json()
        return UserData(
            id_financiador=data["CoberturaPorDefecto"]["IdMutual"],
            id_plan=data["CoberturaPorDefecto"]["IdPlanMutual"],
        )

    def book_appointment(self, appointment_data: dict) -> BookAppointmentResponse:
        url = "https://miportal.sanatorioallende.com/backend/api/turnos/Asignar"

        response = requests.post(
            url, headers={"authorization": self.auth_header}, json=appointment_data
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        data = response.json()

        return BookAppointmentResponse(
            id_turno=data.get("Entidad", {}).get("Id"),
            data=data,
        )

    def cancel_appointment(self, appointment_id: int) -> CancelAppointmentResponse:
        """
        Response format:
        {
            "IsOk": true,
            "Message": "",
            "HasWarnings": false,
            "WarningMessage": "",
            "IdEntidadValidada": 0
        }
        """
        url = "https://miportal.sanatorioallende.com/backend/api/turnos/CancelarTurno"

        data = {
            "IdTurno": appointment_id,
            "Observaciones": "Cancela paciente desde el portal",
            "IdMotivoDeAnulacionTurno": 1,
        }
        response = requests.post(
            url, headers={"authorization": self.auth_header}, json=data
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        data = response.json()

        return CancelAppointmentResponse(
            IsOk=data.get("IsOk", False),  # type: ignore
            Message=data.get("Message", ""),  # type: ignore
            HasWarnings=data.get("HasWarnings", False),  # type: ignore
            WarningMessage=data.get("WarningMessage", ""),  # type: ignore
            IdEntidadValidada=data.get("IdEntidadValidada", 0),  # type: ignore
        )

    @classmethod
    def is_authorized(cls, auth_header: str) -> bool:
        response = requests.get(
            "https://miportal.sanatorioallende.com/backend/api/GestionDeEspera/Totem/ObtenerOpcionesDelTotemPortal",
            headers={"authorization": auth_header},
        )
        return response.status_code == HTTP_OK

    def search_best_date_appointment(self, doctor_data: dict) -> Optional[dict]:
        """Searches the best date for an appointment with the given doctor"""
        response = requests.post(
            "https://miportal.sanatorioallende.com/backend/api/DisponibilidadDeTurnos/ObtenerPrimerTurnoAsignableParaPortalWebConParticular",
            headers={"authorization": self.auth_header},
            json=doctor_data,
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        appointments = self._get_appointment_dates(response.json())
        if not appointments:
            return None

        return min(appointments, key=lambda x: x["datetime"])

    def _get_appointment_dates(self, data: List[dict]) -> List[dict]:
        """Parses the appointments from the response data to get the appointment dates and additional data"""
        appointments = []
        for turno in data.get("PrimerosTurnosDeCadaRecurso", []):  # type: ignore
            date = turno["Fecha"].split("T")[0]
            date = datetime.strptime(date, "%Y-%m-%d")
            hora = turno["Hora"]
            if not hora:
                continue

            hora = datetime.strptime(hora, "%H:%M")
            date_and_time = date.replace(hour=hora.hour, minute=hora.minute)

            # Extract additional appointment data
            appointment_data = {
                "datetime": date_and_time.replace(tzinfo=timezone(timedelta(hours=-3))),
                "duracion_individual": turno.get("DuracionIndividual"),
                "id_plantilla_turno": turno.get("IdPlantillaTurno"),
                "id_item_plantilla": turno.get("IdItemDePlantilla"),
            }

            appointments.append(appointment_data)

        return appointments

    def get_available_appointment_types(
        self, id_especialidad: str, id_servicio: str, id_sucursal: str
    ) -> List[dict]:
        """
        Response format:
        [
            {
                "IdTipoPrestacion": 1,
                "Activo": true,
                "HabilitadaTelemedicina": false,
                "Prefacturables": "420101-CONSULTA MEDICA\n",
                "Id": 5495,
                "Nombre": "CONSULTA"
            },
            {
                "IdTipoPrestacion": 1,
                "Activo": true,
                "HabilitadaTelemedicina": true,
                "Prefacturables": "420109-TELEMEDICINA\n",
                "Id": 6605,
                "Nombre": "CONSULTA TELEMEDICINA"
            }
        ]
        """
        response = requests.get(
            f"https://miportal.sanatorioallende.com/backend/api/PrestacionMedica/ObtenerPorRecursoEspecialidadServicioSucursalParaPortalWeb/0/0/{id_especialidad}/{id_servicio}/{id_sucursal}",
            headers={"authorization": self.auth_header},
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        return response.json()  # type: ignore
