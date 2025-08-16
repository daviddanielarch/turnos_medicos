import json
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from sanatorio_allende.models import Especialidad
from sanatorio_allende.services.data_loader import DataLoader


class Command(BaseCommand):
    help = "Populate the database with doctors parsed from the website"

    def handle(self, *args: Any, **options: Any) -> None:
        especialidades = Especialidad.objects.filter(name="ALERGIA")

        for especialidad in especialidades:
            DataLoader().load_especialidad(especialidad)
