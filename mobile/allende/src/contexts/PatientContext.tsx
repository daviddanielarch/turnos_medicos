import React, { createContext, ReactNode, useContext, useState } from 'react';
import { Patient } from '../../services/apiService';

interface PatientContextType {
    selectedPatient: Patient | null;
    setSelectedPatient: (patient: Patient | null) => void;
    clearSelectedPatient: () => void;
}

const PatientContext = createContext<PatientContextType | undefined>(undefined);

interface PatientProviderProps {
    children: ReactNode;
}

export function PatientProvider({ children }: PatientProviderProps) {
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);

    const clearSelectedPatient = () => {
        setSelectedPatient(null);
    };

    const value: PatientContextType = {
        selectedPatient,
        setSelectedPatient,
        clearSelectedPatient,
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