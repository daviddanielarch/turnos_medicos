from django.core.management.base import BaseCommand
from turnos.models import TipoDeTurno, Doctor
import json


class Command(BaseCommand):
    help = "Populate the database with doctors parsed from the website"

    def handle(self, *args, **options):
        doctor = json.loads(
            """{
            "IdRecurso": 23463,
            "IdTipoRecurso": 1,
            "NumeroMatricula": 23463,
            "Nombre": "BARRERA ROSANA FABIANA",
            "IdEspecialidad": 30,
            "Especialidad": "ALERGIA",
            "IdServicio": 9,
            "Servicio": "ALERGIA",
            "IdSucursal": 2,
            "Sucursal": "CERRO"
        }"""
        )
        doctor = Doctor.from_json(doctor)
        doctor.save()

        tipo_de_turno = TipoDeTurno(id_tipo_turno=5495, name="Consulta", id_servicio=9)
        tipo_de_turno.save()
