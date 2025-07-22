#!/usr/bin/env python3

import json
import logging
from datetime import datetime

import requests

from turnos.selenium_utils import SeleniumSettings, find_request, get_browser

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401


class UnauthorizedException(Exception):
    pass


logger = logging.getLogger(__name__)


class Allende:
    def __init__(
        self, auth_header: str = None, selenium_settings: SeleniumSettings = None
    ):
        self.auth_header = auth_header
        self.selenium_settings = selenium_settings
        self.user_id = None

    def get_user_id(self):
        return self.user_id

    def get_auth_header(self):
        return self.auth_header

    def login(self, user: str, password: str):
        if self.is_authorized(self.auth_header):
            return self.auth_header

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

    @classmethod
    def is_authorized(cls, auth_header: str):
        response = requests.get(
            "https://miportal.sanatorioallende.com/backend/api/GestionDeEspera/Totem/ObtenerOpcionesDelTotemPortal",
            headers={"authorization": auth_header},
        )
        return response.status_code == HTTP_OK

    def search_best_date_appointment(self, doctor_data: dict):
        """Searches the best date for an appointment with the given doctor"""
        response = requests.post(
            "https://miportal.sanatorioallende.com/backend/api/DisponibilidadDeTurnos/ObtenerPrimerTurnoAsignableDeCadaRecursoDelServicioParaPortalWebConParticular",
            headers={"authorization": self.auth_header},
            json=doctor_data,
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        appointments = self._get_appointment_dates(response.json())
        if not appointments:
            return

        return min(appointments)

    def _get_appointment_dates(self, data: list[dict]) -> list[datetime]:
        """Parses the appointments from the response data to get the appointment dates"""
        appointments = []
        for turno in data["PrimerosTurnosDeCadaRecurso"]:
            if not turno["Atiende"]:
                continue

            date = turno["Fecha"].split("T")[0]
            date = datetime.strptime(date, "%Y-%m-%d")
            hora = turno["Hora"]
            if not hora:
                continue

            hora = datetime.strptime(hora, "%H:%M")
            date_and_time = date.replace(hour=hora.hour, minute=hora.minute)

            appointments.append(date_and_time)

        return appointments

    def get_available_doctors(
        self, id_especialidad: str, id_servicio: str, id_sucursal: str
    ):
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
        return response.json()

    def get_available_appointment_types(
        self, id_especialidad: str, id_servicio: str, id_sucursal: str
    ):
        response = requests.get(
            f"https://miportal.sanatorioallende.com/backend/api/PrestacionMedica/ObtenerPorRecursoEspecialidadServicioSucursalParaPortalWeb/0/0/{id_especialidad}/{id_servicio}/{id_sucursal}",
            headers={"authorization": self.auth_header},
        )

        if response.status_code == HTTP_UNAUTHORIZED:
            raise UnauthorizedException()

        return response.json()
