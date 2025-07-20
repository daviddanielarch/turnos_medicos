from django.db import models


SUCURSAL_CHOICES = [
    ("Cerro", "CERRO"),
    ("Nueva Cba", "NUEVA CBA"),
]


class TipoDeTurno(models.Model):
    name = models.CharField(max_length=255)
    id_tipo_turno = models.IntegerField(primary_key=True)
    id_servicio = models.IntegerField(db_index=True)

    def from_json(self, json_data):
        """
        {
            "IdTipoPrestacion": 1,
            "Activo": true,
            "HabilitadaTelemedicina": false,
            "Prefacturables": "420101-CONSULTA MEDICA\n",
            "Id": 5495,
            "Nombre": "CONSULTA"
        },
        """
        self.name = json_data["Nombre"]
        self.id_tipo_turno = json_data["Id"]
        return self

    def __str__(self):
        return f"{self.name}"


class Doctor(models.Model):
    """
    There can be multiple doctors with the same name but differerent sucursal.
    """

    name = models.CharField(max_length=255, db_index=True)
    especialidad = models.CharField(max_length=255)
    servicio = models.CharField(max_length=255)
    sucursal = models.CharField(max_length=255)
    id_recurso = models.IntegerField(primary_key=True)
    id_tipo_recurso = models.IntegerField()
    id_especialidad = models.IntegerField()
    id_sucursal = models.IntegerField()
    id_servicio = models.CharField(max_length=255)

    @classmethod
    def from_json(cls, json_data):
        """
        {
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
        }
        """
        doctor = cls()
        doctor.name = json_data["Nombre"]
        doctor.especialidad = json_data["Especialidad"]
        doctor.servicio = json_data["Servicio"]
        doctor.sucursal = json_data["Sucursal"]
        doctor.id_recurso = json_data["IdRecurso"]
        doctor.id_tipo_recurso = json_data["IdTipoRecurso"]
        doctor.id_especialidad = json_data["IdEspecialidad"]
        doctor.id_sucursal = json_data["IdSucursal"]
        doctor.id_servicio = json_data["IdServicio"]
        return doctor

    def __str__(self):
        return f"{self.name} - {self.especialidad} - {self.sucursal}"


class FindAppointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    tipo_de_turno = models.ForeignKey(TipoDeTurno, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.doctor} - {self.tipo_de_turno}"

    class Meta:
        verbose_name = "Find Appointment"
        verbose_name_plural = "Find Appointments"
        ordering = ["doctor"]


class BestAppointmentFound(models.Model):
    appointment_wanted = models.OneToOneField(FindAppointment, on_delete=models.CASCADE)
    datetime = models.DateTimeField()


class PacienteAllende(models.Model):
    name = models.CharField(max_length=255)
    id_paciente = models.CharField(max_length=255)
    docid = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=2048, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.id_paciente}"

    class Meta:
        verbose_name = "Paciente Allende"
        verbose_name_plural = "Pacientes Allende"
        ordering = ["id_paciente"]
