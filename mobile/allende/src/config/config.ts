import Constants from 'expo-constants';

// Get the API host from environment variables
// For development, you can set EXPO_PUBLIC_API_HOST in your .env file
// For production, this can be set in your deployment environment
export const API_HOST = Constants.expoConfig?.extra?.apiHost ||
    process.env.EXPO_PUBLIC_API_HOST ||
    'http://localhost:8000';


// API endpoints
export const API_ENDPOINTS = {
    DOCTORS: `${API_HOST}/api/doctors/`,
    APPOINTMENT_TYPES: `${API_HOST}/api/appointment-types/`,
    CREATE_APPOINTMENT: `${API_HOST}/api/create-appointment/`,
    FIND_APPOINTMENTS: `${API_HOST}/api/find-appointments/`,
    UPDATE_APPOINTMENT_STATUS: `${API_HOST}/api/update-appointment-status/`,
    BEST_APPOINTMENTS: `${API_HOST}/api/best-appointments/`,
} as const;

// Configuration object
export const config = {
    API_HOST,
    API_ENDPOINTS,
} as const; 