import time

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
        parser.add_argument(
            "--check-receipts",
            action="store_true",
            help="Check push receipts after sending notification",
        )
        parser.add_argument(
            "--receipt-delay",
            type=int,
            default=5,
            help="Delay in seconds before checking receipts (default: 5)",
        )
        parser.add_argument(
            "--detailed-logs",
            action="store_true",
            help="Show detailed receipt logs",
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

            # Check push receipts if requested
            if options["check_receipts"] and result.get("receipt_ids"):
                self.stdout.write(
                    f"\nWaiting {options['receipt_delay']} seconds before checking receipts..."
                )
                time.sleep(options["receipt_delay"])

                self.stdout.write("Checking push receipts...")
                receipt_result = PushNotificationService.check_push_receipts(
                    result["receipt_ids"]
                )

                if receipt_result["success"]:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Receipt check completed for {receipt_result['total_receipts']} notifications"
                        )
                    )

                    # Use the new detailed logging if requested
                    if options["detailed_logs"]:
                        self.stdout.write("\n" + "=" * 50)
                        self.stdout.write("DETAILED RECEIPT LOGS")
                        self.stdout.write("=" * 50)
                        PushNotificationService.log_receipt_details(
                            receipt_result["receipts"]
                        )
                        self.stdout.write("=" * 50 + "\n")

                    # Display receipt details
                    delivered_count = 0
                    failed_count = 0
                    unknown_count = 0

                    for receipt_id, receipt_data in receipt_result["receipts"].items():
                        status = receipt_data["status"]
                        if status == "delivered":
                            delivered_count += 1
                            self.stdout.write(f"  ✓ {receipt_id}: Delivered")

                            # Show additional delivery details if available
                            if options["detailed_logs"]:
                                details = receipt_data.get("details", {})
                                if details.get("deliveryTime"):
                                    self.stdout.write(
                                        f"    Delivery Time: {details['deliveryTime']}"
                                    )
                                if details.get("platform"):
                                    self.stdout.write(
                                        f"    Platform: {details['platform']}"
                                    )
                                if details.get("deviceId"):
                                    self.stdout.write(
                                        f"    Device ID: {details['deviceId']}"
                                    )

                        elif status == "failed":
                            failed_count += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  ✗ {receipt_id}: Failed - {receipt_data.get('error', 'Unknown error')}"
                                )
                            )

                            # Show additional error details if available
                            if options["detailed_logs"]:
                                details = receipt_data.get("details", {})
                                if details.get("errorCode"):
                                    self.stdout.write(
                                        f"    Error Code: {details['errorCode']}"
                                    )
                                if details.get("errorType"):
                                    self.stdout.write(
                                        f"    Error Type: {details['errorType']}"
                                    )
                                if details.get("platform"):
                                    self.stdout.write(
                                        f"    Platform: {details['platform']}"
                                    )
                                if details.get("deviceId"):
                                    self.stdout.write(
                                        f"    Device ID: {details['deviceId']}"
                                    )

                        else:
                            unknown_count += 1
                            self.stdout.write(
                                self.style.WARNING(f"  ? {receipt_id}: Unknown status")
                            )

                            # Show raw data for unknown status
                            if options["detailed_logs"]:
                                raw_data = receipt_data.get("data", {})
                                self.stdout.write(f"    Raw Data: {raw_data}")

                    # Summary with enhanced statistics
                    summary = receipt_result.get("summary", {})
                    self.stdout.write(
                        f"\nReceipt Summary: {summary.get('delivered', delivered_count)} delivered, "
                        f"{summary.get('failed', failed_count)} failed, {summary.get('unknown', unknown_count)} unknown"
                    )

                    # Show additional summary information if available
                    if options["detailed_logs"] and summary:
                        self.stdout.write(
                            f"Total receipts checked: {summary.get('total', receipt_result['total_receipts'])}"
                        )

                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to check receipts: {receipt_result['error']}"
                        )
                    )
            elif options["check_receipts"] and not result.get("receipt_ids"):
                self.stdout.write(
                    self.style.WARNING("No receipt IDs available to check")
                )
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to send notification: {result['error']}")
            )
