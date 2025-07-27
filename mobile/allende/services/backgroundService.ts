import * as BackgroundFetch from 'expo-background-fetch';
import * as Notifications from 'expo-notifications';
import * as TaskManager from 'expo-task-manager';
import { API_ENDPOINTS } from '../app/config';

const BACKGROUND_FETCH_TASK = 'background-fetch-appointments';

// Configure notifications
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
        shouldShowBanner: true,
        shouldShowList: true,
    }),
});

// Register background task
TaskManager.defineTask(BACKGROUND_FETCH_TASK, async () => {
    try {
        console.log('[Background] Checking for new appointments...');

        // Check for appointments found in the last 30 seconds
        const response = await fetch(`${API_ENDPOINTS.FIND_APPOINTMENTS}?seconds=30`);
        const data = await response.json();

        if (data.success && data.appointments && data.appointments.length > 0) {
            console.log(`[Background] Found ${data.appointments.length} new appointments`);

            // Show notification for each new appointment
            for (const appointment of data.appointments) {
                await Notifications.scheduleNotificationAsync({
                    content: {
                        title: '¡Nuevo turno disponible! 🎉',
                        body: `${appointment.name} - ${appointment.especialidad} (${appointment.tipo_de_turno})`,
                        data: { appointment },
                    },
                    trigger: null, // Show immediately
                });
            }

            return BackgroundFetch.BackgroundFetchResult.NewData;
        } else {
            console.log('[Background] No new appointments found');
            return BackgroundFetch.BackgroundFetchResult.NoData;
        }
    } catch (error) {
        console.error('[Background] Error checking appointments:', error);
        return BackgroundFetch.BackgroundFetchResult.Failed;
    }
});

export class BackgroundService {
    private static instance: BackgroundService;
    private isRegistered = false;
    private initializationAttempted = false;

    private constructor() { }

    static getInstance(): BackgroundService {
        if (!BackgroundService.instance) {
            BackgroundService.instance = new BackgroundService();
        }
        return BackgroundService.instance;
    }

    async requestPermissions(): Promise<boolean> {
        try {
            const { status: notificationStatus } = await Notifications.requestPermissionsAsync();

            console.log('Notification permission status:', notificationStatus);

            // Even if permissions are not granted, we'll still try to register the task
            // The system will handle permission requests automatically
            return true;
        } catch (error) {
            console.error('Error requesting permissions:', error);
            return false;
        }
    }

    async startBackgroundCheck(): Promise<boolean> {
        try {
            if (this.isRegistered) {
                console.log('[Background] Service already registered');
                return true;
            }

            if (this.initializationAttempted) {
                console.log('[Background] Initialization already attempted, retrying...');
            }

            this.initializationAttempted = true;

            // Request permissions (but don't fail if not granted)
            await this.requestPermissions();

            // Try to register background fetch task
            try {
                await BackgroundFetch.registerTaskAsync(BACKGROUND_FETCH_TASK, {
                    minimumInterval: 60, // Check every 60 seconds
                    stopOnTerminate: false,
                    startOnBoot: true,
                });

                this.isRegistered = true;
                console.log('[Background] Background check started successfully');
                return true;
            } catch (registerError) {
                console.error('[Background] Error registering task:', registerError);

                // If registration fails, we'll still try to set up notifications
                // and the user can manually check
                console.log('[Background] Will fall back to manual checking');
                return false;
            }
        } catch (error) {
            console.error('[Background] Error starting background check:', error);
            return false;
        }
    }

    async stopBackgroundCheck(): Promise<void> {
        try {
            if (!this.isRegistered) {
                return;
            }

            await BackgroundFetch.unregisterTaskAsync(BACKGROUND_FETCH_TASK);
            this.isRegistered = false;
            console.log('[Background] Background check stopped');
        } catch (error) {
            console.error('[Background] Error stopping background check:', error);
        }
    }

    async checkBackgroundStatus(): Promise<BackgroundFetch.BackgroundFetchStatus | null> {
        try {
            return await BackgroundFetch.getStatusAsync();
        } catch (error) {
            console.error('[Background] Error getting background status:', error);
            return null;
        }
    }

    // Manual check for testing
    async manualCheck(): Promise<boolean> {
        try {
            console.log('[Manual] Checking for new appointments...');

            const response = await fetch(`${API_ENDPOINTS.FIND_APPOINTMENTS}?seconds=30`);
            const data = await response.json();

            if (data.success && data.appointments && data.appointments.length > 0) {
                console.log(`[Manual] Found ${data.appointments.length} new appointments`);

                // Show notification for each new appointment
                for (const appointment of data.appointments) {
                    await Notifications.scheduleNotificationAsync({
                        content: {
                            title: '¡Nuevo turno disponible! 🎉',
                            body: `${appointment.name} - ${appointment.especialidad} (${appointment.tipo_de_turno})`,
                            data: { appointment },
                        },
                        trigger: null, // Show immediately
                    });
                }

                return true;
            } else {
                console.log('[Manual] No new appointments found');
                return false;
            }
        } catch (error) {
            console.error('[Manual] Error checking appointments:', error);
            return false;
        }
    }

    // Force restart the service
    async restart(): Promise<boolean> {
        await this.stopBackgroundCheck();
        this.initializationAttempted = false;
        return await this.startBackgroundCheck();
    }
}

export default BackgroundService.getInstance(); 