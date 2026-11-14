from typing import Callable, List, TypeVar

from sanatorio_allende.allende_api import (
    Allende,
    BookAppointmentResponse,
    CancelAppointmentResponse,
    UnauthorizedException,
)
from sanatorio_allende.models import PacienteAllende
from sanatorio_allende.services.auth import AllendeAuthService

T = TypeVar("T")


class PatientAllende:
    """
    The Allende API on behalf of a patient.

    The patient's stored token expires on Allende's schedule, so it is only a
    cache of the last login: when Allende rejects it, log in again and repeat
    the request, instead of depending on someone else having logged in recently.
    """

    def __init__(self, patient: PacienteAllende):
        self.patient = patient

    def get_doctors(self, pattern: str) -> List[dict]:
        return self._request(lambda allende: allende.get_doctors(pattern=pattern))

    def get_available_appointment_types(
        self, id_especialidad: str, id_servicio: str, id_sucursal: str
    ) -> List[dict]:
        return self._request(
            lambda allende: allende.get_available_appointment_types(
                id_especialidad=id_especialidad,
                id_servicio=id_servicio,
                id_sucursal=id_sucursal,
            )
        )

    def book_appointment(self, appointment_data: dict) -> BookAppointmentResponse:
        return self._request(lambda allende: allende.book_appointment(appointment_data))

    def cancel_appointment(self, appointment_id: int) -> CancelAppointmentResponse:
        return self._request(lambda allende: allende.cancel_appointment(appointment_id))

    def _request(self, request: Callable[[Allende], T]) -> T:
        try:
            return request(Allende(self.patient.token))
        except UnauthorizedException:
            AllendeAuthService(self.patient).login_once()
            return request(Allende(self.patient.token))
