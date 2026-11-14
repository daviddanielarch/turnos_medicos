import time
from typing import Callable, TypeVar

from django.utils import timezone

from sanatorio_allende.allende_api import Allende, UnauthorizedException
from sanatorio_allende.models import PacienteAllende

LOGIN_ATTEMPTS = 3

T = TypeVar("T")


class AllendeAuthService:
    def __init__(self, patient: PacienteAllende):
        self.patient = patient

    def call(self, request: Callable[[Allende], T]) -> T:
        """
        Make a request to Allende on behalf of the patient.

        The stored token expires on Allende's schedule, so it is only a cache of
        the last login: when Allende rejects it, log in again and repeat the
        request, instead of depending on someone else having logged in recently.
        """
        try:
            return request(Allende(self.patient.token))
        except UnauthorizedException:
            self.login_once()
            return request(Allende(self.patient.token))

    def login(self) -> str:
        """Log in, waiting out transient failures. Too slow for a web request."""
        if self.patient.token:
            if not Allende.is_authorized(self.patient.token):
                token_issue_time = self.patient.updated_at
                token_issue_delta_minutes = (
                    timezone.now() - token_issue_time
                ).total_seconds() / 60
                print(f"Token duration: {token_issue_delta_minutes} minutes")

        # Retry login with a simple exponential backoff implementation
        sleep_time = 2
        for attempt in range(1, LOGIN_ATTEMPTS + 1):
            try:
                self.login_once()
                break
            except Exception as e:
                print(f"Error logging in for patient {self.patient.id}: {str(e)}")
                if attempt == LOGIN_ATTEMPTS:
                    raise Exception(
                        f"Error logging in for patient {self.patient.id}: {str(e)}"
                    )
                time.sleep(sleep_time)
                sleep_time *= 2

        return self.patient.token or ""

    def login_once(self) -> None:
        """Log in and store the resulting token and patient data"""
        allende = Allende(self.patient.token)
        allende.login(self.patient.docid, self.patient.password)

        self.patient.token = allende.get_auth_header()

        user_id = allende.get_user_id()
        if user_id:
            self.patient.id_paciente = user_id
            user_data = allende.get_user_data()
            self.patient.id_financiador = user_data.id_financiador
            self.patient.id_plan = user_data.id_plan

        self.patient.save(
            update_fields=[
                "token",
                "id_paciente",
                "id_financiador",
                "id_plan",
                "updated_at",
            ]
        )
