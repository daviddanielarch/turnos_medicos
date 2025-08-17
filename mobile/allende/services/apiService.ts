import { config } from '@/src/config/config';

interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

interface FindAppointmentsResponse {
    appointments: Array<{
        id: number;
        name: string;
        location: string;
        especialidad: string;
        enabled: boolean;
        tipo_de_turno: string;
        desired_timeframe: string;
        doctor_id: number;
        tipo_de_turno_id: number;
    }>;
}

interface Doctor {
    IdRecurso: number;
    IdTipoRecurso: number;
    NumeroMatricula: number;
    Nombre: string;
    IdEspecialidad: number;
    Especialidad: string;
    IdServicio: number;
    Servicio: string;
    IdSucursal: number;
    Sucursal: string;
}

interface DoctorsResponse {
    Especialidades: any[];
    Profesionales: Doctor[];
}

interface AppointmentType {
    IdTipoPrestacion: number;
    Activo: boolean;
    HabilitadaTelemedicina: boolean;
    Prefacturables: string;
    Id: number;
    Nombre: string;
}

interface AppointmentTypesResponse {
    appointment_types: AppointmentType[];
}

interface CreateFindAppointmentResponse {
    success: boolean;
    message: string;
    appointment_id?: number;
}

interface ConfirmAppointmentResponse {
    success: boolean;
    message: string;
}

export interface Patient {
    id: number;
    name: string;
    id_paciente: string | null;
    docid: string;
    updated_at: string | null;
}

interface PatientsResponse {
    patients: Patient[];
}

class ApiService {
    private baseUrl: string;
    private getCredentials: (() => Promise<any>) | null = null;

    constructor() {
        this.baseUrl = config.API_HOST;
    }

    /**
     * Set the credentials getter function from Auth0
     */
    setCredentialsGetter(getCredentials: () => Promise<any>) {
        this.getCredentials = getCredentials;
    }

    /**
     * Make an authenticated API request
     */
    private async makeRequest<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<ApiResponse<T>> {
        try {
            let authHeader = null;

            // Get Auth0 credentials if available
            if (this.getCredentials) {
                try {
                    const credentials = await this.getCredentials();
                    if (credentials?.accessToken) {
                        authHeader = `Bearer ${credentials.accessToken}`;
                    }
                } catch (error) {
                    console.log('No valid credentials available');
                }
            }

            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
                ...(options.headers as Record<string, string> || {}),
            };

            if (authHeader) {
                headers['Authorization'] = authHeader;
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers,
            });

            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    error: data.error || `HTTP ${response.status}: ${response.statusText}`,
                };
            }

            return {
                success: true,
                data,
            };
        } catch (error) {
            console.error('API request error:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
            };
        }
    }

    /**
     * GET request
     */
    async get<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
        let url = endpoint;
        if (params) {
            const searchParams = new URLSearchParams(params);
            url += `?${searchParams.toString()}`;
        }

        console.log('Making GET request to:', `${this.baseUrl}${url}`);

        return this.makeRequest<T>(url, {
            method: 'GET',
        });
    }

    /**
     * POST request
     */
    async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
        return this.makeRequest<T>(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined,
        });
    }

    /**
     * PATCH request
     */
    async patch<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
        return this.makeRequest<T>(endpoint, {
            method: 'PATCH',
            body: data ? JSON.stringify(data) : undefined,
        });
    }

    /**
     * DELETE request
     */
    async delete<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
        return this.makeRequest<T>(endpoint, {
            method: 'DELETE',
            body: data ? JSON.stringify(data) : undefined,
        });
    }

    // API endpoints for the app

    /**
     * Get all doctors
     */
    async getDoctors(patient_id: number, pattern?: string) {
        const params: Record<string, string> = {
            patient_id: patient_id.toString()
        };
        if (pattern) {
            params.pattern = pattern;
        }
        return this.get<{ doctors: DoctorsResponse }>('/api/doctors/', params);
    }

    /**
     * Get appointment types for a doctor
     */
    async getAppointmentTypes(patient_id: number, id_especialidad: string, id_servicio: string, id_sucursal: string) {
        return this.get<AppointmentTypesResponse>('/api/appointment-types/', {
            patient_id: patient_id.toString(),
            id_especialidad,
            id_servicio,
            id_sucursal
        });
    }

    /**
     * Get find appointments
     */
    async getFindAppointments(patient_id?: number) {
        console.log('getFindAppointments called with patient_id:', patient_id);
        const params: Record<string, string> = {};
        if (patient_id) {
            params.patient_id = patient_id.toString();
        }
        console.log('API params:', params);
        return this.get<FindAppointmentsResponse>('/api/find-appointments/', Object.keys(params).length > 0 ? params : undefined);
    }

    /**
     * Create a new find appointment
     */
    async createFindAppointment(data: {
        id_servicio: number;
        id_sucursal: number;
        id_recurso: number;
        id_especialidad: number;
        id_tipo_recurso: number;
        id_prestacion: number;
        id_tipo_prestacion: number;
        nombre_tipo_prestacion: string;
        patient_id: number;
        doctor_name: string;
        servicio: string;
        sucursal: string;
        especialidad: string;
        desired_timeframe?: string;
    }) {
        return this.post<CreateFindAppointmentResponse>('/api/find-appointments/', data);
    }

    /**
     * Update find appointment status
     */
    async updateFindAppointmentStatus(appointmentId: number, active: boolean) {
        return this.patch('/api/find-appointments/', {
            appointment_id: appointmentId,
            active,
        });
    }

    /**
     * Get best appointments
     */
    async getBestAppointments(patient_id?: number) {
        const params: Record<string, string> = {};
        if (patient_id) {
            params.patient_id = patient_id.toString();
        }
        return this.get('/api/best-appointments/', Object.keys(params).length > 0 ? params : undefined);
    }

    /**
     * Mark appointment as not interested
     */
    async markAppointmentNotInterested(appointmentId: number, notInterested: boolean = true) {
        return this.patch('/api/best-appointments/', {
            appointment_id: appointmentId,
            not_interested: notInterested,
        });
    }

    /**
     * Confirm an appointment
     */
    async confirmAppointment(appointmentId: number) {
        return this.post<ConfirmAppointmentResponse>('/api/confirm-appointment/', {
            appointment_id: appointmentId,
        });
    }

    /**
     * Get patients
     */
    async getPatients() {
        return this.get<PatientsResponse>('/api/patients/');
    }

    /**
     * Create a new patient
     */
    async createPatient(data: {
        name: string;
        id_paciente?: string;
        docid: string;
        password: string;
    }) {
        return this.post('/api/patients/', data);
    }

    /**
     * Delete a patient
     */
    async deletePatient(patientId: number) {
        return this.delete('/api/patients/', { patient_id: patientId });
    }

    /**
     * Register device for push notifications
     */
    async registerDevice(data: {
        push_token: string;
        platform?: string;
    }) {
        return this.post('/api/device-registrations/', data);
    }
}

// Export a singleton instance
export const apiService = new ApiService();
export default apiService; 