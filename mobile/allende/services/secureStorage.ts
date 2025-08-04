import * as SecureStore from 'expo-secure-store';
import { Patient } from './apiService';

const STORAGE_KEYS = {
    SELECTED_PATIENT: 'selected_patient',
} as const;

export interface SecureStorageService {
    saveSelectedPatient: (patient: Patient) => Promise<void>;
    getSelectedPatient: () => Promise<Patient | null>;
    clearSelectedPatient: () => Promise<void>;
    clearAllData: () => Promise<void>;
}

class SecureStorageServiceImpl implements SecureStorageService {
    async saveSelectedPatient(patient: Patient): Promise<void> {
        try {
            // Validate that we have a valid patient object
            if (!patient || !patient.id || !patient.name || !patient.docid) {
                throw new Error('Invalid patient data provided');
            }

            const patientData = JSON.stringify(patient);
            await SecureStore.setItemAsync(STORAGE_KEYS.SELECTED_PATIENT, patientData);
            console.log('[SecureStorage] Selected patient saved successfully:', patient.name);
        } catch (error) {
            console.error('[SecureStorage] Error saving selected patient:', error);
            throw error;
        }
    }

    async getSelectedPatient(): Promise<Patient | null> {
        try {
            const patientData = await SecureStore.getItemAsync(STORAGE_KEYS.SELECTED_PATIENT);
            if (patientData) {
                const patient = JSON.parse(patientData) as Patient;

                // Validate the retrieved patient data
                if (!patient || !patient.id || !patient.name || !patient.docid) {
                    console.warn('[SecureStorage] Invalid patient data found, clearing...');
                    await this.clearSelectedPatient();
                    return null;
                }

                console.log('[SecureStorage] Selected patient retrieved successfully:', patient.name);
                return patient;
            }
            return null;
        } catch (error) {
            console.error('[SecureStorage] Error retrieving selected patient:', error);
            // If there's an error reading the data, try to clear it
            try {
                await this.clearSelectedPatient();
            } catch (clearError) {
                console.error('[SecureStorage] Error clearing corrupted data:', clearError);
            }
            return null;
        }
    }

    async clearSelectedPatient(): Promise<void> {
        try {
            await SecureStore.deleteItemAsync(STORAGE_KEYS.SELECTED_PATIENT);
            console.log('[SecureStorage] Selected patient cleared successfully');
        } catch (error) {
            console.error('[SecureStorage] Error clearing selected patient:', error);
            throw error;
        }
    }

    async clearAllData(): Promise<void> {
        try {
            await SecureStore.deleteItemAsync(STORAGE_KEYS.SELECTED_PATIENT);
            console.log('[SecureStorage] All data cleared successfully');
        } catch (error) {
            console.error('[SecureStorage] Error clearing all data:', error);
            throw error;
        }
    }
}

const secureStorage = new SecureStorageServiceImpl();
export default secureStorage; 