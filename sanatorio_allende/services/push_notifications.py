import json
from datetime import datetime
from typing import Any, Dict, List

import requests
from django.conf import settings

from ..models import DeviceRegistration


class PushNotificationService:
    """
    Service to send push notifications using Expo's push notification service
    """

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    @classmethod
    def send_notification(
        cls,
        title: str,
        body: str,
        data: Dict[str, Any] = None,
        sound: str = "default",
        priority: str = "high",
        channel_id: str = None,
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
            devices = DeviceRegistration.objects.filter(is_active=True)

            if not devices.exists():
                return {
                    "success": False,
                    "error": "No active devices registered",
                    "sent_count": 0,
                    "total_devices": 0,
                }

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

            for i in range(0, len(messages), batch_size):
                batch = messages[i : i + batch_size]

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

                        # Check for errors in the response
                        if isinstance(result, list):
                            for item in result:
                                if item.get("status") == "error":
                                    errors.append(
                                        {
                                            "token": item.get("details", {}).get(
                                                "sentTo"
                                            ),
                                            "error": item.get("message"),
                                        }
                                    )
                                else:
                                    total_sent += 1
                        else:
                            # Single message response
                            if result.get("status") == "error":
                                errors.append(
                                    {
                                        "token": result.get("details", {}).get(
                                            "sentTo"
                                        ),
                                        "error": result.get("message"),
                                    }
                                )
                            else:
                                total_sent += 1
                    else:
                        errors.append(
                            {"error": f"HTTP {response.status_code}: {response.text}"}
                        )

                except requests.RequestException as e:
                    errors.append({"error": f"Request failed: {str(e)}"})

            return {
                "success": True,
                "sent_count": total_sent,
                "total_devices": devices.count(),
                "errors": errors,
            }

        except Exception as e:
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

        return cls.send_notification(
            title=title, body=body, data=data, sound="default", priority="normal"
        )
