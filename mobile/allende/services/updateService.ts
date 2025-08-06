import * as Updates from 'expo-updates';

export class UpdateService {
    /**
     * Check for available updates
     */
    static async checkForUpdates(): Promise<boolean> {
        try {
            const update = await Updates.checkForUpdateAsync();
            return update.isAvailable;
        } catch (error) {
            console.error('Error checking for updates:', error);
            return false;
        }
    }

    /**
     * Fetch and apply the latest update
     */
    static async fetchUpdate(): Promise<boolean> {
        try {
            const update = await Updates.fetchUpdateAsync();
            if (update.isNew) {
                await Updates.reloadAsync();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error fetching update:', error);
            return false;
        }
    }

    /**
     * Get the current update channel
     */
    static getChannel(): string {
        return Updates.channel || 'default';
    }

    /**
     * Get the current runtime version
     */
    static getRuntimeVersion(): string {
        return Updates.runtimeVersion || 'unknown';
    }

    /**
     * Check if updates are enabled
     */
    static isEnabled(): boolean {
        return Updates.isEnabled;
    }

    /**
     * Get the current update ID
     */
    static getUpdateId(): string | null {
        return Updates.updateId;
    }

    /**
     * Get the current update manifest
     */
    static getManifest() {
        return Updates.manifest;
    }
} 