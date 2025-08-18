import time
from datetime import datetime

from django.conf import settings

from sanatorio_allende.allende_api import Allende
from sanatorio_allende.models import PacienteAllende
from sanatorio_allende.selenium_utils import SeleniumSettings


class AllendeAuthService:
    def __init__(self, patient: PacienteAllende):
        self.patient = patient

    def login(self) -> str:
        allende = Allende(
            self.patient.token,
            SeleniumSettings(
                hostname=settings.SELENIUM_HOSTNAME,
                port=int(settings.SELENIUM_PORT),
                implicit_wait=int(settings.SELENIUM_IMPLICIT_WAIT),
            ),
        )

        if self.patient.token:
            if not Allende.is_authorized(self.patient.token):
                token_issue_time = self.patient.updated_at
                token_issue_delta_minutes = (
                    datetime.now() - token_issue_time
                ).total_seconds() / 60
                print(f"Token duration: {token_issue_delta_minutes} minutes")

        # Retry login up to 3 times with a simple exponential backoff implementation
        sleep_time = 2
        for attempt in range(3):
            try:
                allende.login(self.patient.docid, self.patient.password)
                break
            except Exception as e:
                if attempt < 2:
                    print(f"Error logging in for patient {self.patient.id}: {str(e)}")
                    time.sleep(sleep_time)
                    sleep_time *= 2
                else:
                    print(f"Error logging in for patient {self.patient.id}: {str(e)}")
                    raise Exception(
                        f"Error logging in for patient {self.patient.id}: {str(e)}"
                    )

        self.patient.token = allende.get_auth_header()

        user_id = allende.get_user_id()
        if user_id:
            self.patient.id_paciente = user_id
            user_data = allende.get_user_data()
            self.patient.id_financiador = user_data["IdFinanciador"]
            self.patient.id_plan = user_data["IdPlan"]

        self.patient.save()

        return self.patient.token or ""
