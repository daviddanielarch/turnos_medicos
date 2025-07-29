from django.core.management.base import BaseCommand

from sanatorio_allende.services.push_notifications import PushNotificationService


class Command(BaseCommand):
    help = "Test push notification service"

    def add_arguments(self, parser):
        parser.add_argument(
            "--appointment",
            action="store_true",
            help="Send appointment notification instead of test notification",
        )

    def handle(self, *args, **options):
        if options["appointment"]:
            # Send appointment notification
            appointment_data = {
                "name": "Dr. Juan Pérez",
                "especialidad": "Cardiología",
                "tipo_de_turno": "CONSULTA",
                "datetime": "2024-01-15 10:30:00",
                "location": "Sucursal Centro",
            }

            self.stdout.write("Sending appointment notification...")
            result = PushNotificationService.send_appointment_notification(
                appointment_data
            )
        else:
            # Send test notification
            self.stdout.write("Sending test notification...")
            result = PushNotificationService.send_test_notification()

        if result["success"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Notification sent successfully! "
                    f"Sent to {result['sent_count']} out of {result['total_devices']} devices"
                )
            )

            if result.get("errors"):
                self.stdout.write(
                    self.style.WARNING(f"Some errors occurred: {result['errors']}")
                )
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to send notification: {result['error']}")
            )
