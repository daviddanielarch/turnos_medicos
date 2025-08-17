#!/usr/bin/env python3

import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from sanatorio_allende.selenium_utils import SeleniumSettings, find_request, get_browser

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401


class UnauthorizedException(Exception):
    pass


logger = logging.getLogger(__name__)


class Allende:
    def __init__(
        self,
        auth_header: Optional[str] = None,
        selenium_settings: Optional[SeleniumSettings] = None,
    ):
        self.auth_header = auth_header
        self.selenium_settings = selenium_settings
        self.user_id = None

    def get_user_id(self) -> Optional[str]:
        return self.user_id

    def get_auth_header(self) -> Optional[str]:
        return self.auth_header

    @classmethod
    def validate_credentials(cls, dni: str, password: str) -> bool:
        data = requests.post(
            "https://miportal.sanatorioallende.com/backend/Token",
            data={
                "UserName": "",
                "Password": base64.b64encode(password.encode("utf-8")).decode("utf-8"),
                "NumeroDocumento": base64.b64encode(dni.encode("utf-8")).decode(
                    "utf-8"
                ),
                "IdTipoDocumento": 1,
                "Sistema": base64.b64encode(b"app-portal-paciente").decode("utf-8"),
                "ReCaptcha": "",
            },
        )
        return data.status_code == HTTP_OK

    def login(self, user: str, password: str) -> str:
        if self.auth_header and self.is_authorized(self.auth_header):
            return self.auth_header

        if not self.selenium_settings:
            raise Exception("Selenium settings are required for login")

        browser = get_browser(
            self.selenium_settings.hostname, self.selenium_settings.port
        )
        browser.implicitly_wait(self.selenium_settings.implicit_wait)

        try:
            # Open the login page URL
            browser.get("https://miportal.sanatorioallende.com/auth/loginPortal")

            # Find the email and password fields
            email_field = browser.find_element("name", "inputNroDocumento")
            password_field = browser.find_element("name", "inputPassword")

            # Enter the email and password
            email_field.send_keys(user)
            password_field.send_keys(password)

            # Find the login button and click it
            login_button = browser.find_element("xpath", "//button[@type='submit']")
            login_button.click()

            request = find_request(browser, "ObtenerTurnosParaPortalPorFiltro")
            auth_header = request.get("headers", {}).get("Authorization")
            # get the user id from the request

            self.user_id = json.loads(request.get("postData", {})).get("IdPaciente")
            if not self.user_id:
                raise Exception("Could not get user id")

            self.auth_header = auth_header

            if not auth_header:
                raise Exception("Check username or password")

        finally:
            browser.close()
            browser.quit()

        return auth_header

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

        return response.json()  # type: ignore

    def get_user_data(self) -> Dict[str, Any]:
        if not self.user_id:
            raise Exception("User id not found")

        response = requests.get(
            f"https://miportal.sanatorioallende.com/backend/api/Paciente/ObtenerPorId/{self.user_id}",
            headers={"authorization": self.auth_header},
        )
        data = response.json()
        return {
            "IdFinanciador": data["CoberturaPorDefecto"]["IdMutual"],
            "IdPlan": data["CoberturaPorDefecto"]["IdPlanMutual"],
        }

    def reservar(self, appointment_data: dict) -> Dict[str, Any]:
        url = "https://miportal.sanatorioallende.com/backend/api/turnos/Asignar"

        response = requests.post(
            url, headers={"authorization": self.auth_header}, json=appointment_data
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        return response.json()  # type: ignore  # type: ignore

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
                "datetime": date_and_time,
                "duracion_individual": turno.get("DuracionIndividual"),
                "id_plantilla_turno": turno.get("IdPlantillaTurno"),
                "id_item_plantilla": turno.get("IdItemDePlantilla"),
            }

            appointments.append(appointment_data)

        return appointments

    def get_available_doctors(
        self, id_especialidad: str, id_servicio: str, id_sucursal: str
    ) -> List[dict]:
        response = requests.get(
            f"https://miportal.sanatorioallende.com/backend/api/recurso/ObtenerTodosDeUnServicioEnSucursalConEspecialidadParaPortalWeb/{id_servicio}/{id_sucursal}/{id_especialidad}/329130/2/1227/66",
            headers={"authorization": self.auth_header},
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        """
        Response is a list of this:
            {
                "Id": 23463,
                "IdTipoRecurso": 1,
                "TipoRecurso": "Profesional",
                "Nombre": "BARRERA ROSANA FABIANA",
                "Atiende": true,
                "VisiblePortalWeb": true,
                "Matricula": 23463,
                "ProfesionalQueAtiende": null
            },
        """
        return response.json()  # type: ignore

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
