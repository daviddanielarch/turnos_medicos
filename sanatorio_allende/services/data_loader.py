from typing import Any, Dict, List, Optional, Tuple

from sanatorio_allende.allende_api import Allende
from sanatorio_allende.models import (
    AppointmentType,
    Doctor,
    Especialidad,
    PacienteAllende,
)
from sanatorio_allende.services.auth import AllendeAuthService


class DataLoader:
    def load_especialidades(
        self, especialidades_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, int]:
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for especialidad_data in especialidades_data:
            id_especialidad = especialidad_data.get("IdEspecialidad")
            id_servicio = especialidad_data.get("IdServicio")
            id_sucursal = especialidad_data.get("IdSucursal")

            if not all([id_especialidad, id_servicio, id_sucursal]):
                print(
                    f"Skipping especialidad with missing required fields: {especialidad_data}"
                )
                skipped_count += 1
                continue

            # Check if especialidad already exists using composite key
            especialidad, created = Especialidad.objects.get_or_create(
                id_especialidad=id_especialidad,
                id_servicio=id_servicio,
                id_sucursal=id_sucursal,
                defaults={
                    "name": especialidad_data.get("Especialidad", ""),
                    "sucursal": especialidad_data.get("Sucursal", ""),
                    "servicio": especialidad_data.get("Servicio", ""),
                },
            )

            if created:
                created_count += 1
            else:
                # Update existing record
                especialidad.name = especialidad_data.get("Especialidad", "")
                especialidad.sucursal = especialidad_data.get("Sucursal", "")
                especialidad.servicio = especialidad_data.get("Servicio", "")
                especialidad.save()
                updated_count += 1

        return created_count, updated_count, skipped_count

    def load_especialidad(self, especialidad: Especialidad) -> None:
        user = PacienteAllende.objects.first()
        if user is None:
            raise ValueError("No PacienteAllende found in database")

        auth_service = AllendeAuthService(user)
        auth_service.login()

        allende = Allende(user.token)
        appointment_types = allende.get_available_appointment_types(
            str(especialidad.id_especialidad),
            str(especialidad.id_servicio),
            str(especialidad.id_sucursal),
        )
        AppointmentType.objects.bulk_create(
            [
                AppointmentType(
                    name=appointment_type["Nombre"],
                    id_tipo_turno=appointment_type["Id"],
                    id_tipo_prestacion=appointment_type["IdTipoPrestacion"],
                    especialidad=especialidad,
                )
                for appointment_type in appointment_types
            ],
            ignore_conflicts=True,
        )

        doctors = allende.get_available_doctors(
            str(especialidad.id_especialidad),
            str(especialidad.id_servicio),
            str(especialidad.id_sucursal),
        )
        Doctor.objects.bulk_create(
            [
                Doctor(
                    name=doctor["Nombre"],
                    especialidad=especialidad,
                    id_recurso=doctor["Id"],
                    id_tipo_recurso=doctor["IdTipoRecurso"],
                )
                for doctor in doctors
            ],
            ignore_conflicts=True,
        )
