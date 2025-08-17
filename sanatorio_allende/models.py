from django.contrib.auth.models import User
from django.db import models


class PacienteAllende(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    id_paciente = models.CharField(max_length=255, null=True, blank=True)
    docid = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=2048, null=True, blank=True)
    id_financiador = models.IntegerField(null=True, blank=True)
    id_plan = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.id_paciente}"

    class Meta:
        verbose_name = "Paciente Allende"
        verbose_name_plural = "Pacientes Allende"
        ordering = ["id_paciente"]


class FindAppointment(models.Model):
    DEFAULT_DESIRED_TIMEFRAME = "anytime"

    patient = models.ForeignKey(PacienteAllende, on_delete=models.CASCADE)
    doctor_name = models.CharField(max_length=255, db_index=True)
    id_servicio = models.IntegerField()
    servicio = models.CharField(max_length=255)
    id_sucursal = models.IntegerField()
    sucursal = models.CharField(max_length=255)
    id_especialidad = models.IntegerField()
    especialidad = models.CharField(max_length=255)
    id_recurso = models.IntegerField()
    id_tipo_recurso = models.IntegerField()

    id_prestacion = models.IntegerField()
    id_tipo_prestacion = models.IntegerField()
    nombre_tipo_prestacion = models.CharField(max_length=255)

    desired_timeframe = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=DEFAULT_DESIRED_TIMEFRAME,
        choices=[
            ("1 week", "1 week"),
            ("2 weeks", "2 weeks"),
            ("3 weeks", "3 weeks"),
            ("anytime", "anytime"),
        ],
    )
    active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.doctor_name} - {self.especialidad}"

    class Meta:
        verbose_name = "Find Appointment"
        verbose_name_plural = "Find Appointments"
        ordering = ["doctor_name"]


class BestAppointmentFound(models.Model):
    patient = models.ForeignKey(PacienteAllende, on_delete=models.CASCADE)
    appointment_wanted = models.ForeignKey(FindAppointment, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    not_interested = models.BooleanField(default=False)

    # Fields for appointment confirmation
    duracion_individual = models.IntegerField(null=True, blank=True)
    id_plantilla_turno = models.IntegerField(null=True, blank=True)
    id_item_plantilla = models.IntegerField(null=True, blank=True)

    # Fields for confirmed appointment
    confirmed_id_turno = models.IntegerField(null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.appointment_wanted.doctor_name} - {self.datetime}"

    class Meta:
        # Allow multiple BestAppointmentFound per FindAppointment
        unique_together = [["appointment_wanted", "patient", "datetime"]]


class DeviceRegistration(models.Model):
    """
    Model to store device registration for push notifications
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    push_token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=50, default="expo")  # expo, ios, android
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.platform} - {self.push_token[:20]}..."

    class Meta:
        verbose_name = "Device Registration"
        verbose_name_plural = "Device Registrations"
        ordering = ["-created_at"]
