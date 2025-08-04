import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import requests
from django.contrib.auth.models import User

from sanatorio_allende.models import DeviceRegistration

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service to send push notifications using Expo's push notification service
    """

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    EXPO_RECEIPT_URL = "https://exp.host/--/api/v2/push/getReceipts"

    @classmethod
    def send_notification(
        cls,
        title: str,
        body: str,
        data: Dict[str, Any] = None,
        sound: str = "default",
        priority: str = "high",
        channel_id: str = None,
        user: User = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to all registered devices

        Args:
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            sound: Sound to play (default, none, or custom sound file)
            priority: Priority level (default, normal, high)
            channel_id: Android channel ID for notification grouping

        Returns:
            Dict with success status and results
        """
        try:
            # Get all active device registrations
            devices = DeviceRegistration.objects.filter(is_active=True, user=user)

            if not devices.exists():
                logger.warning("No active devices registered for push notifications")
                return {
                    "success": False,
                    "error": "No active devices registered",
                    "sent_count": 0,
                    "total_devices": 0,
                }

            logger.info(
                f"Sending push notification to {devices.count()} active devices"
            )
            logger.info(f"Notification: '{title}' - '{body}'")

            # Prepare notification payload
            notification_payload = {
                "title": title,
                "body": body,
                "sound": sound,
                "priority": priority,
            }

            if data:
                notification_payload["data"] = data

            if channel_id:
                notification_payload["channelId"] = channel_id

            # Prepare messages for each device
            messages = []
            for device in devices:
                message = {"to": device.push_token, **notification_payload}
                messages.append(message)

            # Send notifications in batches (Expo recommends max 100 per request)
            batch_size = 100
            total_sent = 0
            errors = []
            receipt_ids = []

            for i in range(0, len(messages), batch_size):
                batch = messages[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(messages) + batch_size - 1) // batch_size

                logger.info(
                    f"Sending batch {batch_num}/{total_batches} with {len(batch)} messages"
                )

                try:
                    response = requests.post(
                        cls.EXPO_PUSH_URL,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        data=json.dumps(batch),
                    )

                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Batch {batch_num} response received successfully")

                        # Check for errors in the response
                        if isinstance(result, list):
                            for item in result:
                                if item.get("status") == "error":
                                    error_info = {
                                        "token": item.get("details", {}).get("sentTo"),
                                        "error": item.get("message"),
                                        "details": item.get("details", {}),
                                    }
                                    errors.append(error_info)
                                    logger.error(
                                        f"Push notification error: {error_info}"
                                    )
                                else:
                                    total_sent += 1
                                    # Collect receipt IDs for successful sends
                                    if item.get("status") == "ok":
                                        receipt_id = item.get("id")
                                        if receipt_id:
                                            receipt_ids.append(receipt_id)
                                            logger.debug(
                                                f"Receipt ID collected: {receipt_id}"
                                            )
                        else:
                            # Single message response - check if it has a data field with list
                            if result.get("data") and isinstance(result["data"], list):
                                for item in result["data"]:
                                    if item.get("status") == "error":
                                        error_info = {
                                            "token": item.get("details", {}).get(
                                                "sentTo"
                                            ),
                                            "error": item.get("message"),
                                            "details": item.get("details", {}),
                                        }
                                        errors.append(error_info)
                                        logger.error(
                                            f"Push notification error: {error_info}"
                                        )
                                    else:
                                        total_sent += 1
                                        # Collect receipt ID for successful send
                                        if item.get("status") == "ok":
                                            receipt_id = item.get("id")
                                            if receipt_id:
                                                receipt_ids.append(receipt_id)
                                                logger.debug(
                                                    f"Receipt ID collected: {receipt_id}"
                                                )
                            elif result.get("status") == "error":
                                error_info = {
                                    "token": result.get("details", {}).get("sentTo"),
                                    "error": result.get("message"),
                                    "details": result.get("details", {}),
                                }
                                errors.append(error_info)
                                logger.error(f"Push notification error: {error_info}")
                            else:
                                total_sent += 1
                                # Collect receipt ID for successful send
                                if result.get("status") == "ok":
                                    receipt_id = result.get("id")
                                    if receipt_id:
                                        receipt_ids.append(receipt_id)
                                        logger.debug(
                                            f"Receipt ID collected: {receipt_id}"
                                        )
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        errors.append({"error": error_msg})
                        logger.error(f"Push notification HTTP error: {error_msg}")

                except requests.RequestException as e:
                    error_msg = f"Request failed: {str(e)}"
                    errors.append({"error": error_msg})
                    logger.error(f"Push notification request exception: {error_msg}")

            logger.info(
                f"Push notification sending completed. Sent: {total_sent}, Errors: {len(errors)}, Receipt IDs: {len(receipt_ids)}"
            )

            return {
                "success": True,
                "sent_count": total_sent,
                "total_devices": devices.count(),
                "errors": errors,
                "receipt_ids": receipt_ids,
            }

        except Exception as e:
            logger.error(f"Push notification sending failed with exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sent_count": 0,
                "total_devices": 0,
            }

    @classmethod
    def send_appointment_notification(
        cls, appointment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification for new appointment found

        Args:
            appointment_data: Dictionary containing appointment information

        Returns:
            Dict with notification results
        """
        title = "¡Nuevo turno disponible! 🎉"
        body = f"{appointment_data.get('name', 'Doctor')} - {appointment_data.get('especialidad', 'Especialidad')} ({appointment_data.get('tipo_de_turno', 'Tipo de turno')})"

        data = {"type": "new_appointment", "appointment": appointment_data}

        logger.info(
            f"Sending appointment notification for: {appointment_data.get('name', 'Unknown')}"
        )

        return cls.send_notification(
            title=title, body=body, data=data, sound="default", priority="high"
        )

    @classmethod
    def send_test_notification(cls) -> Dict[str, Any]:
        """
        Send a test notification to verify the service is working

        Returns:
            Dict with notification results
        """
        title = "Test Notification"
        body = "This is a test notification from the backend"

        data = {"type": "test", "timestamp": str(datetime.now())}

        logger.info("Sending test notification")

        return cls.send_notification(
            title=title, body=body, data=data, sound="default", priority="normal"
        )

    @classmethod
    def check_push_receipts(cls, receipt_ids: List[str]) -> Dict[str, Any]:
        """
        Check the status of push notification receipts

        Args:
            receipt_ids: List of receipt IDs to check

        Returns:
            Dict with receipt status information
        """
        try:
            if not receipt_ids:
                logger.warning("No receipt IDs provided for checking")
                return {
                    "success": False,
                    "error": "No receipt IDs provided",
                    "receipts": {},
                }

            logger.info(f"Checking {len(receipt_ids)} push notification receipts")

            # Prepare the request payload
            payload = {"ids": receipt_ids}

            response = requests.post(
                cls.EXPO_RECEIPT_URL,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                data=json.dumps(payload),
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("Receipt check response received successfully")

                # Process the receipts
                receipts = {}
                # The receipt data is nested under 'data' field
                receipt_data = result.get("data", {})

                delivered_count = 0
                failed_count = 0
                unknown_count = 0

                for receipt_id, receipt_info in receipt_data.items():
                    logger.debug(f"Processing receipt {receipt_id}: {receipt_info}")

                    if receipt_info.get("status") == "ok":
                        delivered_count += 1
                        receipt_details = receipt_info.get("details", {})
                        receipts[receipt_id] = {
                            "status": "delivered",
                            "details": receipt_details,
                            "delivery_time": receipt_details.get("deliveryTime"),
                            "delivery_status": receipt_details.get("deliveryStatus"),
                            "device_id": receipt_details.get("deviceId"),
                            "platform": receipt_details.get("platform"),
                            "app_id": receipt_details.get("appId"),
                        }
                        logger.info(f"Receipt {receipt_id} delivered successfully")

                    elif receipt_info.get("status") == "error":
                        failed_count += 1
                        error_message = receipt_info.get("message", "Unknown error")
                        error_details = receipt_info.get("details", {})
                        receipts[receipt_id] = {
                            "status": "failed",
                            "error": error_message,
                            "details": error_details,
                            "error_code": error_details.get("errorCode"),
                            "error_type": error_details.get("errorType"),
                            "device_id": error_details.get("deviceId"),
                            "platform": error_details.get("platform"),
                            "app_id": error_details.get("appId"),
                        }
                        logger.error(f"Receipt {receipt_id} failed: {error_message}")

                    else:
                        unknown_count += 1
                        receipts[receipt_id] = {
                            "status": "unknown",
                            "data": receipt_info,
                            "raw_status": receipt_info.get("status"),
                            "message": receipt_info.get("message"),
                            "details": receipt_info.get("details", {}),
                        }
                        logger.warning(
                            f"Receipt {receipt_id} has unknown status: {receipt_info}"
                        )

                # Log summary statistics
                logger.info(
                    f"Receipt check completed - Delivered: {delivered_count}, Failed: {failed_count}, Unknown: {unknown_count}"
                )

                # Log detailed receipt information
                if delivered_count > 0:
                    logger.info(
                        f"Successfully delivered notifications: {delivered_count}"
                    )
                if failed_count > 0:
                    logger.warning(f"Failed notifications: {failed_count}")
                if unknown_count > 0:
                    logger.warning(f"Unknown status notifications: {unknown_count}")

                return {
                    "success": True,
                    "receipts": receipts,
                    "total_receipts": len(receipt_ids),
                    "delivered_count": delivered_count,
                    "failed_count": failed_count,
                    "unknown_count": unknown_count,
                    "summary": {
                        "delivered": delivered_count,
                        "failed": failed_count,
                        "unknown": unknown_count,
                        "total": len(receipt_ids),
                    },
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Receipt check HTTP error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "receipts": {},
                }

        except Exception as e:
            logger.error(f"Receipt check failed with exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "receipts": {},
            }

    @classmethod
    def log_receipt_details(cls, receipts: Dict[str, Any]) -> None:
        """
        Log detailed information about receipt statuses

        Args:
            receipts: Dictionary containing receipt information
        """
        if not receipts:
            logger.info("No receipts to log")
            return

        logger.info("=== RECEIPT DETAILS ===")

        for receipt_id, receipt_info in receipts.items():
            status = receipt_info.get("status", "unknown")

            if status == "delivered":
                details = receipt_info.get("details", {})
                logger.info(f"✅ Receipt {receipt_id}: DELIVERED")
                logger.info(f"   - Delivery Time: {details.get('deliveryTime')}")
                logger.info(f"   - Platform: {details.get('platform')}")
                logger.info(f"   - Device ID: {details.get('deviceId')}")
                logger.info(f"   - App ID: {details.get('appId')}")

            elif status == "failed":
                error_msg = receipt_info.get("error", "Unknown error")
                details = receipt_info.get("details", {})
                logger.error(f"❌ Receipt {receipt_id}: FAILED")
                logger.error(f"   - Error: {error_msg}")
                logger.error(f"   - Error Code: {details.get('errorCode')}")
                logger.error(f"   - Error Type: {details.get('errorType')}")
                logger.error(f"   - Platform: {details.get('platform')}")
                logger.error(f"   - Device ID: {details.get('deviceId')}")

            else:
                logger.warning(f"❓ Receipt {receipt_id}: UNKNOWN STATUS")
                logger.warning(f"   - Raw Data: {receipt_info}")

        logger.info("=== END RECEIPT DETAILS ===")
