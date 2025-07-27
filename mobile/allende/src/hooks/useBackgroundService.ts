import { useEffect, useState } from 'react';
import backgroundService from '../../services/backgroundService';

export const useBackgroundService = () => {
    const [isEnabled, setIsEnabled] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            const status = await backgroundService.checkBackgroundStatus();
            setIsEnabled(status !== null);
        } catch (error) {
            console.error('Error checking background status:', error);
        }
    };

    const startService = async () => {
        setIsLoading(true);
        try {
            const success = await backgroundService.startBackgroundCheck();
            if (success) {
                setIsEnabled(true);
            }
            return success;
        } catch (error) {
            console.error('Error starting background service:', error);
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    const stopService = async () => {
        setIsLoading(true);
        try {
            await backgroundService.stopBackgroundCheck();
            setIsEnabled(false);
            return true;
        } catch (error) {
            console.error('Error stopping background service:', error);
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    const toggleService = async () => {
        if (isEnabled) {
            return await stopService();
        } else {
            return await startService();
        }
    };

    const testNotification = async () => {
        setIsLoading(true);
        try {
            return await backgroundService.manualCheck();
        } catch (error) {
            console.error('Error testing notification:', error);
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    return {
        isEnabled,
        isLoading,
        startService,
        stopService,
        toggleService,
        testNotification,
        checkStatus,
    };
}; 