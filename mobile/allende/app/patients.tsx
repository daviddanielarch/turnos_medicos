import CustomHeader from '@/src/components/CustomHeader';
import { COLORS } from '@/src/constants/constants';
import { useAuth0Context } from '@/src/contexts/Auth0Context';
import { usePatientContext } from '@/src/contexts/PatientContext';
import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    FlatList,
    Modal,
    RefreshControl,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import apiService, { Patient } from '../services/apiService';

export default function PatientsScreen() {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [showAddModal, setShowAddModal] = useState(false);
    const [deletingPatientId, setDeletingPatientId] = useState<number | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        id_paciente: '',
        docid: '',
        password: '',
    });
    const [submitting, setSubmitting] = useState(false);

    const { getCredentials } = useAuth0Context();
    const { selectedPatient, setSelectedPatient, isLoading: patientContextLoading } = usePatientContext();

    useEffect(() => {
        // Set up API service with credentials
        apiService.setCredentialsGetter(getCredentials);
        loadPatients();
    }, [getCredentials]);

    const loadPatients = async () => {
        try {
            setLoading(true);
            const response = await apiService.getPatients();

            if (response.success && response.data?.patients) {
                setPatients(response.data.patients);
            } else {
                console.error('Failed to load patients:', response.error);
                Alert.alert('Error', 'No se pudieron cargar los pacientes');
            }
        } catch (error) {
            console.error('Error loading patients:', error);
            Alert.alert('Error', 'Error al cargar los pacientes');
        } finally {
            setLoading(false);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await loadPatients();
        setRefreshing(false);
    };

    const handleAddPatient = async () => {
        if (!formData.name || !formData.docid || !formData.password) {
            Alert.alert('Error', 'Por favor completa todos los campos requeridos');
            return;
        }

        try {
            setSubmitting(true);
            const response = await apiService.createPatient(formData);

            if (response.success) {
                Alert.alert('Éxito', 'Paciente agregado correctamente');
                setShowAddModal(false);
                resetForm();
                loadPatients();
            } else {
                Alert.alert('Error', response.error || 'Error al agregar paciente');
            }
        } catch (error) {
            console.error('Error adding patient:', error);
            Alert.alert('Error', 'Error al agregar paciente');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeletePatient = (patient: Patient) => {
        Alert.alert(
            'Eliminar Paciente',
            `¿Estás seguro de que quieres eliminar a ${patient.name}?`,
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Eliminar',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            setDeletingPatientId(patient.id);
                            const response = await apiService.deletePatient(patient.id);

                            if (response.success) {
                                Alert.alert('Éxito', 'Paciente eliminado correctamente');
                                // If the deleted patient was selected, clear the selection
                                if (selectedPatient?.id === patient.id) {
                                    await setSelectedPatient(null);
                                }
                                loadPatients();
                            } else {
                                Alert.alert('Error', response.error || 'Error al eliminar paciente');
                            }
                        } catch (error) {
                            console.error('Error deleting patient:', error);
                            Alert.alert('Error', 'Error al eliminar paciente');
                        } finally {
                            setDeletingPatientId(null);
                        }
                    },
                },
            ]
        );
    };

    const handleSelectPatient = async (patient: Patient) => {
        if (selectedPatient?.id === patient.id) {
            await setSelectedPatient(null);
        } else {
            await setSelectedPatient(patient);
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            id_paciente: '',
            docid: '',
            password: '',
        });
    };

    const renderPatientItem = ({ item }: { item: Patient }) => {
        const isSelected = selectedPatient?.id === item.id;

        return (
            <TouchableOpacity
                style={[
                    styles.patientCard,
                    isSelected && styles.patientCardSelected
                ]}
                onPress={() => handleSelectPatient(item)}
            >
                <View style={styles.patientInfo}>
                    <View style={styles.patientHeader}>
                        <Text style={styles.patientName}>{item.name}</Text>
                    </View>
                    <Text style={styles.patientDetails}>
                        DNI: {item.docid}
                    </Text>
                    <Text style={styles.patientDate}>
                        Actualizado: {item.updated_at ? new Date(item.updated_at).toLocaleDateString('es-AR') : 'N/A'}
                    </Text>
                </View>
                <TouchableOpacity
                    style={[
                        styles.deleteButton,
                        deletingPatientId === item.id && styles.deleteButtonDisabled
                    ]}
                    onPress={() => handleDeletePatient(item)}
                    disabled={deletingPatientId === item.id}
                >
                    {deletingPatientId === item.id ? (
                        <ActivityIndicator size="small" color="white" />
                    ) : (
                        <Ionicons name="trash-outline" size={20} color="white" />
                    )}
                </TouchableOpacity>
            </TouchableOpacity>
        );
    };

    const renderEmptyState = () => (
        <View style={styles.emptyState}>
            <Ionicons name="people-outline" size={64} color="#ccc" />
            <Text style={styles.emptyStateTitle}>No hay pacientes</Text>
            <Text style={styles.emptyStateSubtitle}>
                Agrega tu primer paciente para comenzar
            </Text>
        </View>
    );

    return (
        <View style={styles.container}>
            <CustomHeader
                title="Pacientes"
                showUserInfo={true}
                showLogoutButton={true}
                showPatientInfo={true}
            />

            <View style={styles.content}>

                {loading || patientContextLoading ? (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color={COLORS.PRIMARY} />
                        <Text style={styles.loadingText}>
                            {loading ? 'Cargando pacientes...' : 'Cargando configuración...'}
                        </Text>
                    </View>
                ) : (
                    <FlatList
                        data={patients}
                        renderItem={renderPatientItem}
                        keyExtractor={(item) => item.id.toString()}
                        contentContainerStyle={styles.listContainer}
                        refreshControl={
                            <RefreshControl
                                refreshing={refreshing}
                                onRefresh={onRefresh}
                                colors={[COLORS.PRIMARY]}
                            />
                        }
                        ListEmptyComponent={renderEmptyState}
                    />
                )}
            </View>

            {/* Floating Action Button */}
            <TouchableOpacity
                style={styles.floatingAddButton}
                onPress={() => setShowAddModal(true)}
            >
                <Ionicons name="add" size={24} color="white" />
            </TouchableOpacity>

            {/* Add Patient Modal */}
            <Modal
                visible={showAddModal}
                animationType="slide"
                presentationStyle="pageSheet"
            >
                <View style={styles.modalContainer}>
                    <View style={styles.modalHeader}>
                        <Text style={styles.modalTitle}>Agregar Paciente</Text>
                        <TouchableOpacity
                            onPress={() => {
                                setShowAddModal(false);
                                resetForm();
                            }}
                        >
                            <Ionicons name="close" size={24} color="#666" />
                        </TouchableOpacity>
                    </View>

                    <ScrollView style={styles.modalContent}>
                        <View style={styles.formGroup}>
                            <Text style={styles.label}>Nombre *</Text>
                            <TextInput
                                style={styles.input}
                                value={formData.name}
                                onChangeText={(text) => setFormData({ ...formData, name: text })}
                                placeholder="Nombre completo del paciente"
                                autoCapitalize="words"
                            />
                        </View>

                        <View style={styles.formGroup}>
                            <Text style={styles.label}>DNI *</Text>
                            <TextInput
                                style={styles.input}
                                value={formData.docid}
                                onChangeText={(text) => setFormData({ ...formData, docid: text })}
                                placeholder="Número de documento"
                                keyboardType="numeric"
                            />
                        </View>

                        <View style={styles.formGroup}>
                            <Text style={styles.label}>Contraseña *</Text>
                            <TextInput
                                style={styles.input}
                                value={formData.password}
                                onChangeText={(text) => setFormData({ ...formData, password: text })}
                                placeholder="Contraseña"
                                secureTextEntry
                            />
                        </View>
                    </ScrollView>

                    <View style={styles.modalFooter}>
                        <TouchableOpacity
                            style={styles.cancelButton}
                            onPress={() => {
                                setShowAddModal(false);
                                resetForm();
                            }}
                        >
                            <Text style={styles.cancelButtonText}>Cancelar</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={[
                                styles.saveButton,
                                submitting && styles.saveButtonDisabled
                            ]}
                            onPress={handleAddPatient}
                            disabled={submitting}
                        >
                            {submitting ? (
                                <ActivityIndicator size="small" color="white" />
                            ) : (
                                <Text style={styles.saveButtonText}>Guardar</Text>
                            )}
                        </TouchableOpacity>
                    </View>
                </View>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f8f9fa',
    },
    content: {
        flex: 1,
        padding: 16,
    },
    floatingAddButton: {
        position: 'absolute',
        bottom: 20,
        right: 20,
        backgroundColor: COLORS.PRIMARY,
        width: 56,
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 8,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
    },
    header: {
        flexDirection: 'row',
        marginLeft: 160,
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,

    },
    sectionTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
    },
    addButton: {
        backgroundColor: COLORS.PRIMARY,
        width: 44,
        height: 44,
        borderRadius: 22,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    selectedPatientBanner: {
        backgroundColor: COLORS.PRIMARY,
        padding: 12,
        borderRadius: 8,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: 16,
    },
    selectedPatientText: {
        color: 'white',
        fontSize: 14,
        fontWeight: '500',
        flex: 1,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 12,
        fontSize: 16,
        color: '#666',
    },
    listContainer: {
        flexGrow: 1,
    },
    patientCard: {
        backgroundColor: 'white',
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        flexDirection: 'row',
        alignItems: 'center',
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    patientCardSelected: {
        borderWidth: 2,
        borderColor: COLORS.PRIMARY,
        backgroundColor: '#f0f8ff',
    },
    patientInfo: {
        flex: 1,
    },
    patientHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 4,
    },
    patientName: {
        fontSize: 18,
        fontWeight: '600',
        color: '#333',
        flex: 1,
    },
    selectedIndicator: {
        marginLeft: 8,
    },
    patientDetails: {
        fontSize: 14,
        color: '#666',
        marginBottom: 2,
    },
    patientDate: {
        fontSize: 12,
        color: '#999',
    },
    deleteButton: {
        backgroundColor: '#dc3545',
        padding: 12,
        borderRadius: 8,
        marginLeft: 12,
    },
    deleteButtonDisabled: {
        opacity: 0.7,
    },
    emptyState: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyStateTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: '#666',
        marginTop: 16,
        marginBottom: 8,
    },
    emptyStateSubtitle: {
        fontSize: 16,
        color: '#999',
        textAlign: 'center',
        paddingHorizontal: 32,
    },
    modalContainer: {
        flex: 1,
        backgroundColor: 'white',
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
    },
    modalTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
    },
    modalContent: {
        flex: 1,
        padding: 20,
    },
    formGroup: {
        marginBottom: 20,
    },
    label: {
        fontSize: 16,
        fontWeight: '500',
        color: '#333',
        marginBottom: 8,
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        backgroundColor: '#f9f9f9',
    },
    modalFooter: {
        flexDirection: 'row',
        padding: 20,
        borderTopWidth: 1,
        borderTopColor: '#eee',
        gap: 12,
    },
    cancelButton: {
        flex: 1,
        padding: 16,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#ddd',
        alignItems: 'center',
    },
    cancelButtonText: {
        fontSize: 16,
        color: '#666',
        fontWeight: '500',
    },
    saveButton: {
        flex: 1,
        backgroundColor: COLORS.PRIMARY,
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
    },
    saveButtonDisabled: {
        opacity: 0.7,
    },
    saveButtonText: {
        fontSize: 16,
        color: 'white',
        fontWeight: '500',
    },
}); 