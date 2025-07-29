from django.db import models


class Especialidad(models.Model):
    name = models.CharField(max_length=255)
    id_especialidad = models.IntegerField()
    id_servicio = models.IntegerField()
    id_sucursal = models.IntegerField()
    sucursal = models.CharField(max_length=255)
    servicio = models.CharField(max_length=255)

    def from_json(self, json_data):
        self.name = json_data["Especialidad"]
        self.id_especialidad = json_data["IdEspecialidad"]
        self.id_servicio = json_data["IdServicio"]
        self.id_sucursal = json_data["IdSucursal"]
        self.sucursal = json_data["Sucursal"]
        self.servicio = json_data["Servicio"]
        return self

    def __str__(self):
        return f"{self.name} - {self.sucursal}"

    class Meta:
        unique_together = ["id_especialidad", "id_sucursal", "id_servicio"]


class AppointmentType(models.Model):
    name = models.CharField(max_length=255)
    id_tipo_turno = models.IntegerField()
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)

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

    class Meta:
        unique_together = ["id_tipo_turno", "especialidad"]


class Doctor(models.Model):
    """
    There can be multiple doctors with the same name but differerent sucursal.
    """

    name = models.CharField(max_length=255, db_index=True)
    id_recurso = models.IntegerField()
    id_tipo_recurso = models.IntegerField()
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.especialidad} - {self.especialidad.sucursal}"

    class Meta:
        unique_together = ["id_recurso", "especialidad"]


class FindAppointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    tipo_de_turno = models.ForeignKey(AppointmentType, on_delete=models.CASCADE)
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
    id_paciente = models.CharField(max_length=255, null=True, blank=True)
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


class DeviceRegistration(models.Model):
    """
    Model to store device registration for push notifications
    """

    push_token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=50, default="expo")  # expo, ios, android
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.platform} - {self.push_token[:20]}..."

    class Meta:
        verbose_name = "Device Registration"
        verbose_name_plural = "Device Registrations"
        ordering = ["-created_at"]
