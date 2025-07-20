#!/usr/bin/env python3

import logging
from datetime import datetime

import requests
from selenium import webdriver

from turnos.selenium_utils import find_request

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401


class UnauthorizedException(Exception):
    pass


logger = logging.getLogger(__name__)


class Allende:
    def __init__(self, auth_header: str = None):
        self.auth_header = auth_header

    @classmethod
    def login(self, browser: webdriver.Chrome, user: str, password: str):
        if self.is_authorized():
            return self.auth_header

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

        request = find_request(self.browser, "ObtenerTurnosParaPortalPorFiltro")
        auth_header = request.get("headers", {}).get("Authorization")
        if not auth_header:
            raise Exception("Check username or password")

        self.auth_header = auth_header
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
