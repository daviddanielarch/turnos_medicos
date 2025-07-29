import { config } from "@/src/config/config";
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';

export class PushNotificationService {
    private static instance: PushNotificationService;
    private pushToken: string | null = null;

    private constructor() { }

    static getInstance(): PushNotificationService {
        if (!PushNotificationService.instance) {
            PushNotificationService.instance = new PushNotificationService();
        }
        return PushNotificationService.instance;
    }

    async requestPermissions(): Promise<boolean> {
        try {
            const { status } = await Notifications.requestPermissionsAsync();
            console.log('[Push] Notification permission status:', status);
            return status === 'granted';
        } catch (error) {
            console.error('[Push] Error requesting permissions:', error);
            return false;
        }
    }

    async getPushToken(): Promise<string | null> {
        try {
            if (this.pushToken) {
                return this.pushToken;
            }

            const token = await Notifications.getExpoPushTokenAsync({
                projectId: Constants?.expoConfig?.extra?.eas?.projectId ?? Constants?.easConfig?.projectId,
            });

            this.pushToken = token.data;
            console.log('[Push] Push token obtained:', this.pushToken);
            return this.pushToken;
        } catch (error) {
            console.error('[Push] Error getting push token:', error);
            return null;
        }
    }

    async registerDeviceWithBackend(): Promise<boolean> {
        try {
            const token = await this.getPushToken();
            if (!token) {
                console.error('[Push] No push token available');
                return false;
            }

            const response = await fetch(`${config.API_HOST}/api/register-device/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    push_token: token,
                    platform: 'expo',
                }),
            });

            const data = await response.json();

            if (data.success) {
                console.log('[Push] Device registered successfully with backend');
                return true;
            } else {
                console.error('[Push] Failed to register device:', data.error);
                return false;
            }
        } catch (error) {
            console.error('[Push] Error registering device with backend:', error);
            return false;
        }
    }

    async unregisterDeviceFromBackend(): Promise<boolean> {
        try {
            const token = await this.getPushToken();
            if (!token) {
                return true;
            }

            const response = await fetch(`${config.API_HOST}/api/unregister-device/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    push_token: token,
                }),
            });

            const data = await response.json();

            if (data.success) {
                console.log('[Push] Device unregistered successfully from backend');
                this.pushToken = null;
                return true;
            } else {
                console.error('[Push] Failed to unregister device:', data.error);
                return false;
            }
        } catch (error) {
            console.error('[Push] Error unregistering device from backend:', error);
            return false;
        }
    }

    setNotificationHandler() {
        Notifications.setNotificationHandler({
            handleNotification: async (notification) => {
                console.log('[Push] Notification received:', notification);

                return {
                    shouldShowAlert: true,
                    shouldPlaySound: true,
                    shouldSetBadge: false,
                    shouldShowBanner: true,
                    shouldShowList: true,
                };
            },
        });
    }

    // Add notification response listener
    addNotificationResponseListener(callback: (response: Notifications.NotificationResponse) => void) {
        return Notifications.addNotificationResponseReceivedListener(callback);
    }

    // Add notification received listener
    addNotificationReceivedListener(callback: (notification: Notifications.Notification) => void) {
        return Notifications.addNotificationReceivedListener(callback);
    }
}

export default PushNotificationService.getInstance(); 