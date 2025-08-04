import React, { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { Patient } from '../../services/apiService';
import secureStorage from '../../services/secureStorage';

interface PatientContextType {
    selectedPatient: Patient | null;
    setSelectedPatient: (patient: Patient | null) => void;
    clearSelectedPatient: () => void;
    isLoading: boolean;
}

const PatientContext = createContext<PatientContextType | undefined>(undefined);

interface PatientProviderProps {
    children: ReactNode;
}

export function PatientProvider({ children }: PatientProviderProps) {
    const [selectedPatient, setSelectedPatientState] = useState<Patient | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Load selected patient from secure storage on mount
    useEffect(() => {
        const loadSelectedPatient = async () => {
            try {
                setIsLoading(true);
                const savedPatient = await secureStorage.getSelectedPatient();
                if (savedPatient) {
                    setSelectedPatientState(savedPatient);
                    console.log('[PatientContext] Loaded selected patient from secure storage:', savedPatient.name);
                }
            } catch (error) {
                console.error('[PatientContext] Error loading selected patient:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadSelectedPatient();
    }, []);

    const setSelectedPatient = async (patient: Patient | null) => {
        try {
            setSelectedPatientState(patient);

            if (patient) {
                await secureStorage.saveSelectedPatient(patient);
                console.log('[PatientContext] Selected patient saved to secure storage:', patient.name);
            } else {
                await secureStorage.clearSelectedPatient();
                console.log('[PatientContext] Selected patient cleared from secure storage');
            }
        } catch (error) {
            console.error('[PatientContext] Error saving selected patient:', error);
            // Still update the state even if storage fails
            setSelectedPatientState(patient);
        }
    };

    const clearSelectedPatient = async () => {
        await setSelectedPatient(null);
    };

    const value: PatientContextType = {
        selectedPatient,
        setSelectedPatient,
        clearSelectedPatient,
        isLoading,
    };

    return (
        <PatientContext.Provider value={value}>
            {children}
        </PatientContext.Provider>
    );
}

export function usePatientContext(): PatientContextType {
    const context = useContext(PatientContext);
    if (context === undefined) {
        throw new Error('usePatientContext must be used within a PatientProvider');
    }
    return context;
} 