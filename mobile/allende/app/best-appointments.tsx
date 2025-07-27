import { API_ENDPOINTS } from "@/src/config/config";
import { COLORS } from "@/src/constants/constants";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "@react-navigation/native";
import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Alert, RefreshControl, ScrollView, Text, TouchableOpacity, View } from "react-native";
import backgroundService from "../services/backgroundService";

interface BestAppointment {
    id: number;
    doctor_name: string;
    especialidad: string;
    location: string;
    tipo_de_turno: string;
    best_datetime: string;
}

export default function BestAppointments() {
    const [bestAppointments, setBestAppointments] = useState<BestAppointment[]>([]);
    const [loading, setLoading] = useState(false);
    const [testingNotification, setTestingNotification] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    // Fetch best appointments when component mounts
    useEffect(() => {
        fetchBestAppointments();
    }, []);

    // Refresh best appointments when tab comes into focus
    useFocusEffect(
        useCallback(() => {
            fetchBestAppointments();
        }, [])
    );

    const fetchBestAppointments = async () => {
        setLoading(true);
        try {
            const response = await fetch(API_ENDPOINTS.BEST_APPOINTMENTS);
            const data = await response.json();

            if (data.success) {
                setBestAppointments(data.best_appointments);
            } else {
                console.error('Failed to fetch best appointments:', data.error);
                console.error(API_ENDPOINTS.BEST_APPOINTMENTS);
                Alert.alert('Error', 'Failed to load best appointments');
            }
        } catch (error) {
            console.error('Error fetching best appointments:', error);
            console.error(API_ENDPOINTS.BEST_APPOINTMENTS);
            Alert.alert('Error', 'Network error while loading best appointments');
        } finally {
            setLoading(false);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await fetchBestAppointments();
        setRefreshing(false);
    };

    const testNotification = async () => {
        setTestingNotification(true);
        try {
            const hasNewAppointments = await backgroundService.manualCheck();
            if (hasNewAppointments) {
                Alert.alert('Éxito', 'Se encontraron nuevos turnos y se envió la notificación');
            } else {
                Alert.alert('Info', 'No se encontraron nuevos turnos en los últimos 30 segundos');
            }
        } catch (error) {
            console.error('Error testing notification:', error);
            Alert.alert('Error', 'Ocurrió un error al probar la notificación');
        } finally {
            setTestingNotification(false);
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
            minute: '2-digit',
        });
    };

    if (loading) {
        return (
            <View style={{ flex: 1, paddingTop: 50, backgroundColor: '#f8fafc', justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color={COLORS.PRIMARY} />
                <Text style={{ fontSize: 16, color: '#6b7280', marginTop: 16 }}>
                    Cargando mejores turnos...
                </Text>
            </View>
        );
    }

    if (bestAppointments.length === 0) {
        return (
            <View style={{ flex: 1, paddingTop: 50, backgroundColor: '#f8fafc', justifyContent: 'center', alignItems: 'center' }}>
                <Ionicons name="calendar-outline" size={64} color="#9ca3af" />
                <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, textAlign: 'center' }}>
                    No se encontraron mejores turnos
                </Text>
                <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 8, textAlign: 'center', paddingHorizontal: 32 }}>
                    Los mejores turnos encontrados aparecerán aquí cuando estén disponibles
                </Text>
            </View>
        );
    }

    return (
        <View style={{ flex: 1, paddingTop: 50, backgroundColor: '#f8fafc' }}>
            <View style={styles.header}>
                <View style={styles.headerContent}>
                    <View>
                        <Text style={styles.headerTitle}>Mejores Turnos Encontrados</Text>
                        <Text style={styles.headerSubtitle}>
                            {bestAppointments.length} turno{bestAppointments.length !== 1 ? 's' : ''} encontrado{bestAppointments.length !== 1 ? 's' : ''}
                        </Text>
                    </View>
                    <TouchableOpacity
                        style={[styles.notificationButton, testingNotification && styles.notificationButtonDisabled]}
                        onPress={testNotification}
                        disabled={testingNotification}
                    >
                        <Ionicons
                            name={testingNotification ? "hourglass" : "notifications"}
                            size={20}
                            color={testingNotification ? "#9ca3af" : COLORS.PRIMARY}
                        />
                    </TouchableOpacity>
                </View>
            </View>

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

                        <View style={styles.statusContainer}>
                            <View style={styles.statusBadge}>
                                <Ionicons name="checkmark-circle" size={16} color="#10b981" />
                                <Text style={styles.statusText}>Mejor turno disponible</Text>
                            </View>
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
    notificationButton: {
        backgroundColor: '#f3f4f6',
        padding: 8,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#e5e7eb',
    },
    notificationButtonDisabled: {
        backgroundColor: '#f9fafb',
        borderColor: '#f3f4f6',
    },
    container: {
        flex: 1,
        paddingHorizontal: 20,
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
}; 