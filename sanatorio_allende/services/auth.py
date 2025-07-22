from django.conf import settings

from sanatorio_allende.appointments import Allende
from sanatorio_allende.models import PacienteAllende
from sanatorio_allende.selenium_utils import SeleniumSettings


class AllendeAuthService:
    def __init__(self, user: PacienteAllende):
        self.user = user

    def login(self):
        allende = Allende(
            self.user.token,
            SeleniumSettings(
                hostname=settings.SELENIUM_HOSTNAME,
                port=settings.SELENIUM_PORT,
                implicit_wait=settings.SELENIUM_IMPLICIT_WAIT,
            ),
        )
        allende.login(self.user.docid, self.user.password)
        self.user.token = allende.get_auth_header()

        user_id = allende.get_user_id()
        if user_id:
            self.user.id_paciente = user_id

        self.user.save()

        return self.user.token
