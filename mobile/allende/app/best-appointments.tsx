import CustomHeader from "@/src/components/CustomHeader";
import { COLORS } from "@/src/constants/constants";
import { useAuth0Context } from "@/src/contexts/Auth0Context";
import { usePatientContext } from "@/src/contexts/PatientContext";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "@react-navigation/native";
import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Alert, RefreshControl, ScrollView, Text, TouchableOpacity, View } from "react-native";
import apiService from "../services/apiService";

interface BestAppointment {
    id: number;
    doctor_name: string;
    especialidad: string;
    location: string;
    tipo_de_turno: string;
    best_datetime: string;
    confirmed: boolean;
    confirmed_at: string | null;
}

export default function BestAppointments() {
    const [bestAppointments, setBestAppointments] = useState<BestAppointment[]>([]);
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [processingAppointment, setProcessingAppointment] = useState<number | null>(null);
    const [confirmingAppointment, setConfirmingAppointment] = useState<number | null>(null);
    const [cancelingAppointment, setCancelingAppointment] = useState<number | null>(null);
    const { isAuthenticated } = useAuth0Context();
    const { selectedPatient } = usePatientContext();

    // Fetch best appointments when component mounts and user is authenticated
    useEffect(() => {
        if (isAuthenticated && selectedPatient) {
            fetchBestAppointments();
        }
    }, [isAuthenticated, selectedPatient]);

    // Refresh best appointments when tab comes into focus and user is authenticated
    useFocusEffect(
        useCallback(() => {
            if (isAuthenticated && selectedPatient) {
                fetchBestAppointments();
            }
        }, [isAuthenticated, selectedPatient])
    );

    const fetchBestAppointments = async () => {
        if (!selectedPatient) {
            console.log('No patient selected');
            return;
        }

        setLoading(true);
        try {
            const response = await apiService.getBestAppointments(selectedPatient.id);

            if (response.success && response.data) {
                setBestAppointments((response.data as any).best_appointments);
            } else {
                console.error('Failed to fetch best appointments:', response.error);
                Alert.alert('Error', 'Hubo un problema con la conexión. Intenta nuevamente.');
            }
        } catch (error) {
            console.error('Error fetching best appointments:', error);
            Alert.alert('Error', 'Hubo un problema con la conexión. Intenta nuevamente.');
        } finally {
            setLoading(false);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await fetchBestAppointments();
        setRefreshing(false);
    };

    const handleNotInterested = async (appointmentId: number) => {
        setProcessingAppointment(appointmentId);
        try {
            const response = await apiService.markAppointmentNotInterested(appointmentId);

            if (response.success) {
                // Remove the appointment from the local state
                setBestAppointments(prev => prev.filter(appointment => appointment.id !== appointmentId));
            } else {
                console.error('Failed to mark appointment as not interested:', response.error);
            }
        } catch (error) {
            console.error('Error marking appointment as not interested:', error);
        } finally {
            setProcessingAppointment(null);
        }
    };

    const handleConfirmAppointment = async (appointmentId: number) => {
        setConfirmingAppointment(appointmentId);
        try {
            const response = await apiService.confirmAppointment(appointmentId);

            if (response.success) {
                setBestAppointments(prev => prev.map(appointment =>
                    appointment.id === appointmentId
                        ? { ...appointment, confirmed: true, confirmed_at: new Date().toISOString() }
                        : appointment
                ));
            } else {
                console.error('Failed to confirm appointment:', response.error);
                Alert.alert('Error', 'Hubo un problema con la conexión. Intenta nuevamente.');
            }
        } catch (error) {
            console.error('Error confirming appointment:', error);
            Alert.alert('Error', 'Hubo un problema con la conexión. Intenta nuevamente.');
        } finally {
            setConfirmingAppointment(null);
        }
    };

    const handleCancelAppointment = async (appointmentId: number) => {
        setCancelingAppointment(appointmentId);
        try {
            const response = await apiService.cancelAppointment(appointmentId);

            if (response.success) {
                // Remove the appointment from the local state
                setBestAppointments(prev => prev.filter(appointment => appointment.id !== appointmentId));
            } else {
                console.error('Failed to cancel appointment:', response.error);
                Alert.alert('Error', 'Hubo un problema con la conexión. Intenta nuevamente.');
            }
        } catch (error) {
            console.error('Error canceling appointment:', error);
            Alert.alert('Error', 'Hubo un problema con la conexión. Intenta nuevamente.');
        } finally {
            setCancelingAppointment(null);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-AR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (!isAuthenticated) {
        return (
            <View style={{ flex: 1, backgroundColor: '#f8fafc', justifyContent: 'center', alignItems: 'center' }}>
                <Ionicons name="lock-closed-outline" size={64} color="#9ca3af" />
                <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, textAlign: 'center', fontWeight: '500' }}>
                    Inicia sesión para ver mejores turnos
                </Text>
                <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 8, textAlign: 'center', paddingHorizontal: 32 }}>
                    Necesitas estar autenticado para ver los mejores turnos encontrados
                </Text>
            </View>
        );
    }

    // Show patient selection required message if no patient is selected
    if (!selectedPatient) {
        return (
            <View style={{ flex: 1, backgroundColor: '#f8fafc', justifyContent: 'center', alignItems: 'center' }}>
                <Ionicons name="person-outline" size={64} color="#9ca3af" />
                <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, textAlign: 'center', fontWeight: '500' }}>
                    Selecciona un paciente
                </Text>
                <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 8, textAlign: 'center', paddingHorizontal: 32 }}>
                    Necesitas seleccionar un paciente para ver sus mejores turnos
                </Text>
            </View>
        );
    }

    if (loading) {
        return (
            <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
                <CustomHeader title="Mejores turnos" />
                <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                    <ActivityIndicator size="large" color={COLORS.PRIMARY} />
                    <Text style={{ fontSize: 16, color: '#6b7280', marginTop: 16 }}>
                        Cargando mejores turnos...
                    </Text>
                </View>
            </View>
        );
    }

    if (bestAppointments.length === 0) {
        return (
            <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
                <CustomHeader title="Mejores turnos" />
                <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                    <Ionicons name="calendar-outline" size={64} color="#9ca3af" />
                    <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, textAlign: 'center' }}>
                        No se encontraron mejores turnos
                    </Text>
                    <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 8, textAlign: 'center', paddingHorizontal: 32 }}>
                        Los mejores turnos encontrados aparecerán aquí cuando estén disponibles
                    </Text>
                </View>
            </View>
        );
    }

    return (
        <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
            <CustomHeader title="Mejores turnos" />

            <ScrollView
                style={styles.container}
                showsVerticalScrollIndicator={false}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.PRIMARY]} />
                }
            >
                {bestAppointments.map((appointment) => (
                    <View key={appointment.id} style={styles.card}>
                        <View style={styles.cardHeader}>
                            <View style={styles.doctorInfo}>
                                <Text style={styles.doctorName}>{appointment.doctor_name}</Text>
                                <Text style={styles.specialty}>{appointment.especialidad}</Text>
                                <Text style={styles.location}>{appointment.location}</Text>
                            </View>
                            <View style={styles.appointmentType}>
                                <Text style={styles.appointmentTypeText}>{appointment.tipo_de_turno}</Text>
                            </View>
                        </View>

                        <View style={styles.datetimeContainer}>
                            <Ionicons name="time-outline" size={20} color={COLORS.PRIMARY} />
                            <Text style={styles.datetimeText}>
                                {formatDate(appointment.best_datetime)}
                            </Text>
                        </View>

                        <View style={styles.cardFooter}>
                            <View style={styles.statusContainer}>
                                {appointment.confirmed ? (
                                    <View style={styles.statusBadge}>
                                        <Ionicons name="checkmark-circle" size={16} color="#10b981" />
                                        <Text style={styles.statusText}>Confirmado</Text>
                                    </View>
                                ) : (
                                    <TouchableOpacity
                                        style={[
                                            styles.confirmButton,
                                            confirmingAppointment === appointment.id && styles.confirmButtonDisabled
                                        ]}
                                        onPress={() => handleConfirmAppointment(appointment.id)}
                                        disabled={confirmingAppointment === appointment.id}
                                    >
                                        {confirmingAppointment === appointment.id ? (
                                            <ActivityIndicator size="small" color="white" />
                                        ) : (
                                            <>
                                                <Ionicons name="checkmark-circle" size={16} color="white" />
                                                <Text style={styles.confirmButtonText}>Confirmar</Text>
                                            </>
                                        )}
                                    </TouchableOpacity>
                                )}
                            </View>

                            {!appointment.confirmed ? (
                                <TouchableOpacity
                                    style={[
                                        styles.notInterestedButton,
                                        processingAppointment === appointment.id && styles.notInterestedButtonDisabled
                                    ]}
                                    onPress={() => handleNotInterested(appointment.id)}
                                    disabled={processingAppointment === appointment.id}
                                >
                                    {processingAppointment === appointment.id ? (
                                        <ActivityIndicator size="small" color="#ef4444" />
                                    ) : (
                                        <>
                                            <Ionicons name="close-circle-outline" size={16} color="#ef4444" />
                                            <Text style={styles.notInterestedButtonText}>No me interesa</Text>
                                        </>
                                    )}
                                </TouchableOpacity>
                            ) : (
                                <TouchableOpacity
                                    style={[
                                        styles.cancelButton,
                                        cancelingAppointment === appointment.id && styles.cancelButtonDisabled
                                    ]}
                                    onPress={() => handleCancelAppointment(appointment.id)}
                                    disabled={cancelingAppointment === appointment.id}
                                >
                                    {cancelingAppointment === appointment.id ? (
                                        <ActivityIndicator size="small" color="#dc2626" />
                                    ) : (
                                        <>
                                            <Ionicons name="close-circle" size={16} color="#dc2626" />
                                            <Text style={styles.cancelButtonText}>Cancelar</Text>
                                        </>
                                    )}
                                </TouchableOpacity>
                            )}
                        </View>
                    </View>
                ))}
            </ScrollView>
        </View>
    );
}

const styles = {
    header: {
        paddingHorizontal: 20,
        paddingBottom: 20,
    },
    headerContent: {
        flexDirection: 'row' as const,
        justifyContent: 'space-between' as const,
        alignItems: 'flex-start' as const,
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: 'bold' as const,
        color: '#1f2937',
        marginBottom: 4,
    },
    headerSubtitle: {
        fontSize: 16,
        color: '#6b7280',
    },
    container: {
        flex: 1,
        paddingHorizontal: 20,
        paddingVertical: 20,
    },
    card: {
        backgroundColor: 'white',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 3.84,
        elevation: 5,
    },
    cardHeader: {
        flexDirection: 'row' as const,
        justifyContent: 'space-between' as const,
        alignItems: 'flex-start' as const,
        marginBottom: 12,
    },
    doctorInfo: {
        flex: 1,
    },
    doctorName: {
        fontSize: 18,
        fontWeight: '600' as const,
        color: '#1f2937',
        marginBottom: 4,
    },
    specialty: {
        fontSize: 14,
        color: '#6b7280',
        marginBottom: 2,
    },
    location: {
        fontSize: 14,
        color: '#6b7280',
    },
    appointmentType: {
        backgroundColor: COLORS.PRIMARY,
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 6,
    },
    appointmentTypeText: {
        color: 'white',
        fontSize: 12,
        fontWeight: '600' as const,
    },
    datetimeContainer: {
        flexDirection: 'row' as const,
        alignItems: 'center' as const,
        marginBottom: 12,
        paddingVertical: 8,
        paddingHorizontal: 12,
        backgroundColor: '#f8fafc',
        borderRadius: 8,
    },
    datetimeText: {
        marginLeft: 8,
        fontSize: 14,
        color: '#374151',
        fontWeight: '500' as const,
    },
    statusContainer: {
        flexDirection: 'row' as const,
        justifyContent: 'flex-start' as const,
    },
    statusBadge: {
        flexDirection: 'row' as const,
        alignItems: 'center' as const,
        backgroundColor: '#ecfdf5',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 6,
    },
    statusText: {
        marginLeft: 4,
        fontSize: 12,
        color: '#065f46',
        fontWeight: '500' as const,
    },
    cardFooter: {
        flexDirection: 'row' as const,
        justifyContent: 'space-between' as const,
        alignItems: 'center' as const,
        marginTop: 8,
    },
    notInterestedButton: {
        flexDirection: 'row' as const,
        alignItems: 'center' as const,
        backgroundColor: '#fef2f2',
        borderWidth: 1,
        borderColor: '#fecaca',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 6,
    },
    notInterestedButtonDisabled: {
        opacity: 0.6,
    },
    notInterestedButtonText: {
        marginLeft: 4,
        fontSize: 12,
        color: '#ef4444',
        fontWeight: '500' as const,
    },
    confirmButton: {
        flexDirection: 'row' as const,
        alignItems: 'center' as const,
        backgroundColor: COLORS.PRIMARY,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 6,
    },
    confirmButtonDisabled: {
        opacity: 0.6,
    },
    confirmButtonText: {
        marginLeft: 4,
        fontSize: 12,
        color: 'white',
        fontWeight: '500' as const,
    },
    cancelButton: {
        flexDirection: 'row' as const,
        alignItems: 'center' as const,
        backgroundColor: '#fef2f2',
        borderWidth: 1,
        borderColor: '#fecaca',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 6,
    },
    cancelButtonDisabled: {
        opacity: 0.6,
    },
    cancelButtonText: {
        marginLeft: 4,
        fontSize: 12,
        color: '#dc2626',
        fontWeight: '500' as const,
    },
}; 