import time

from django.conf import settings

from sanatorio_allende.appointments import Allende
from sanatorio_allende.models import PacienteAllende
from sanatorio_allende.selenium_utils import SeleniumSettings


class AllendeAuthService:
    def __init__(self, user: PacienteAllende):
        self.user = user

    def login(self) -> str:
        allende = Allende(
            self.user.token,
            SeleniumSettings(
                hostname=settings.SELENIUM_HOSTNAME,
                port=int(settings.SELENIUM_PORT),
                implicit_wait=int(settings.SELENIUM_IMPLICIT_WAIT),
            ),
        )

        # Retry login up to 3 times with a simple exponential backoff implementation
        sleep_time = 2
        for attempt in range(3):
            try:
                allende.login(self.user.docid, self.user.password)
                break
            except Exception as e:
                if attempt < 2:
                    print(f"Error logging in for patient {self.user.id}: {str(e)}")
                    time.sleep(sleep_time)
                    sleep_time *= 2
                else:
                    print(f"Error logging in for patient {self.user.id}: {str(e)}")
                    raise Exception(
                        f"Error logging in for patient {self.user.id}: {str(e)}"
                    )

        self.user.token = allende.get_auth_header()

        user_id = allende.get_user_id()
        if user_id:
            self.user.id_paciente = user_id
            user_data = allende.get_user_data()
            self.user.id_financiador = user_data["IdFinanciador"]
            self.user.id_plan = user_data["IdPlan"]

        self.user.save()

        return self.user.token or ""
