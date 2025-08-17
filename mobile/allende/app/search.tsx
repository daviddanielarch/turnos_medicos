import CustomHeader from "@/src/components/CustomHeader";
import { COLORS } from "@/src/constants/constants";
import { usePatientContext } from "@/src/contexts/PatientContext";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useCallback, useRef, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, Text, TextInput, TouchableOpacity, View } from "react-native";
import apiService from "../services/apiService";

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

interface ServiceOption {
    id: string;
    name: string;
    IdTipoPrestacion: number;
    Nombre: string;
}

interface TimeframeOption {
    value: string;
    label: string;
}

const TIMEFRAME_OPTIONS: TimeframeOption[] = [
    { value: "anytime", label: "Cualquier momento" },
    { value: "1 week", label: "1 semana" },
    { value: "2 weeks", label: "2 semanas" },
    { value: "3 weeks", label: "3 semanas" },
];

export default function Search() {
    const [searchText, setSearchText] = useState("");
    const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
    const [selectedService, setSelectedService] = useState<ServiceOption | null>(null);
    const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeOption>(TIMEFRAME_OPTIONS[0]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [showServiceDropdown, setShowServiceDropdown] = useState(false);
    const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false);
    const [filteredDoctors, setFilteredDoctors] = useState<Doctor[]>([]);
    const [serviceOptions, setServiceOptions] = useState<ServiceOption[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingServices, setLoadingServices] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);
    const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const { selectedPatient } = usePatientContext();

    // Cleanup function to clear timeout and abort requests
    const cleanup = useCallback(() => {
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
    }, []);

    // Cleanup on unmount
    React.useEffect(() => {
        return cleanup;
    }, [cleanup]);


    const fetchAppointmentTypes = async (doctor: Doctor) => {
        if (!selectedPatient) {
            Alert.alert('Error', 'No patient selected. Please select a patient first.');
            return;
        }

        setLoadingServices(true);
        try {
            const response = await apiService.getAppointmentTypes(
                selectedPatient.id,
                doctor.IdEspecialidad.toString(),
                doctor.IdServicio.toString(),
                doctor.IdSucursal.toString()
            );

            if (response.success && response.data) {
                const appointmentTypes = response.data.appointment_types;
                // Transform the response to match our interface
                const transformedTypes = appointmentTypes.map((type) => ({
                    id: type.Id.toString(),
                    name: type.Nombre,
                    IdTipoPrestacion: type.IdTipoPrestacion,
                    Nombre: type.Nombre,
                }));
                setServiceOptions(transformedTypes);
            } else {
                console.error('Failed to fetch appointment types:', response.error);
            }
        } catch (error) {
            console.error('Error fetching appointment types:', error);
        } finally {
            setLoadingServices(false);
        }
    };

    const performSearch = useCallback(async (searchTerm: string) => {
        if (!selectedPatient) {
            Alert.alert('Error', 'No patient selected. Please select a patient first.');
            return;
        }

        // Cancel any ongoing request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Create new abort controller for this request
        abortControllerRef.current = new AbortController();

        setLoading(true);
        try {
            const response = await apiService.getDoctors(selectedPatient.id, searchTerm);

            if (response.success && response.data) {
                const doctorsData = response.data.doctors;

                if (doctorsData && doctorsData.Profesionales) {
                    setFilteredDoctors(doctorsData.Profesionales);
                    setShowDropdown(true);
                } else {
                    setFilteredDoctors([]);
                    setShowDropdown(false);
                }
            } else {
                console.error('Failed to search doctors:', response.error);
                setFilteredDoctors([]);
                setShowDropdown(false);
            }
        } catch (error) {
            // Don't show error if request was aborted
            if (error instanceof Error && error.name === 'AbortError') {
                console.log('Request was aborted');
                return;
            }
            console.error('Error searching doctors:', error);
            setFilteredDoctors([]);
            setShowDropdown(false);
        } finally {
            setLoading(false);
        }
    }, [selectedPatient]);

    const handleSearch = useCallback((text: string) => {
        setSearchText(text);

        // Clear results if text is empty
        if (text.trim() === "") {
            setFilteredDoctors([]);
            setShowDropdown(false);
            return;
        }

        // Only trigger search after 4 characters
        if (text.trim().length < 4) {
            setFilteredDoctors([]);
            setShowDropdown(false);
            return;
        }

        // Clear previous debounce timeout
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        // Debounce the search - wait 300ms after user stops typing
        debounceTimeoutRef.current = setTimeout(() => {
            performSearch(text.trim());
        }, 300);
    }, [performSearch]);

    const selectDoctor = (doctor: Doctor) => {
        setSelectedDoctor(doctor);
        setSearchText(doctor.Nombre);
        setFilteredDoctors([]);
        setShowDropdown(false);
        setSelectedService(null);
        fetchAppointmentTypes(doctor);
    };

    const selectService = (service: ServiceOption) => {
        setSelectedService(service);
        setShowServiceDropdown(false);
    };

    const selectTimeframe = (timeframe: TimeframeOption) => {
        setSelectedTimeframe(timeframe);
        setShowTimeframeDropdown(false);
    };

    const clearSelection = () => {
        setSelectedDoctor(null);
        setSelectedService(null);
        setSelectedTimeframe(TIMEFRAME_OPTIONS[0]);
        setSearchText("");
        setFilteredDoctors([]);
        setServiceOptions([]);
    };

    const handleAdd = async () => {
        if (selectedDoctor && selectedService) {
            if (!selectedPatient) {
                Alert.alert('Error', 'No patient selected. Please select a patient first.');
                return;
            }

            if (!selectedPatient.id) {
                Alert.alert('Error', 'Selected patient has no valid ID.');
                return;
            }

            try {
                const response = await apiService.createFindAppointment({
                    id_servicio: selectedDoctor.IdServicio,
                    id_sucursal: selectedDoctor.IdSucursal,
                    id_recurso: selectedDoctor.IdRecurso,
                    id_especialidad: selectedDoctor.IdEspecialidad,
                    id_tipo_recurso: selectedDoctor.IdTipoRecurso,
                    id_prestacion: parseInt(selectedService.id),
                    id_tipo_prestacion: selectedService.IdTipoPrestacion,
                    nombre_tipo_prestacion: selectedService.Nombre,
                    patient_id: selectedPatient.id,
                    doctor_name: selectedDoctor.Nombre,
                    servicio: selectedDoctor.Servicio,
                    sucursal: selectedDoctor.Sucursal,
                    especialidad: selectedDoctor.Especialidad,
                    desired_timeframe: selectedTimeframe.value
                });

                if (response.success) {
                    console.log('Appointment created successfully:', response.message);
                    clearSelection();
                    router.push("/");
                } else {
                    console.error('Failed to create appointment:', response.error);
                    Alert.alert('Error', response.error || 'Failed to create appointment');
                }
            } catch (error) {
                console.error('Error creating appointment:', error);
                Alert.alert('Error', 'Network error while creating appointment');
            }
        }
    };

    return (
        <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
            <CustomHeader title="Buscar" />

            {/* Search Section */}
            <ScrollView
                style={{ flex: 1 }}
                contentContainerStyle={{ padding: 20 }}
                showsVerticalScrollIndicator={false}
                keyboardShouldPersistTaps="handled"
            >
                {/* Search Input */}
                <View style={{
                    backgroundColor: 'white',
                    borderRadius: 16,
                    paddingHorizontal: 20,
                    paddingVertical: 16,
                    marginBottom: 24,
                    flexDirection: 'row',
                    alignItems: 'center',
                    shadowColor: '#000',
                    shadowOffset: { width: 0, height: 2 },
                    shadowOpacity: 0.1,
                    shadowRadius: 8,
                    elevation: 3,
                    borderWidth: 1,
                    borderColor: '#e5e7eb',
                }}>
                    <Ionicons name="search" size={22} color="#6b7280" style={{ marginRight: 12 }} />
                    <TextInput
                        style={{
                            flex: 1,
                            fontSize: 16,
                            color: '#111827',
                            outline: 'none'
                        }}
                        placeholder="Medico o especialidad"
                        placeholderTextColor="#9ca3af"
                        value={searchText}
                        onChangeText={handleSearch}
                        onFocus={() => {
                            // Only show dropdown if there are results or if user is typing
                            if (filteredDoctors.length > 0 || searchText.trim().length >= 4) {
                                setShowDropdown(true);
                            }
                        }}
                        underlineColorAndroid="transparent"
                    />
                    {searchText.length > 0 && (
                        <TouchableOpacity onPress={clearSelection} style={{ padding: 4 }}>
                            <Ionicons name="close-circle" size={20} color="#6b7280" />
                        </TouchableOpacity>
                    )}
                </View>

                {/* Loading State */}
                {loading && (
                    <View style={{
                        backgroundColor: 'white',
                        borderRadius: 16,
                        padding: 32,
                        marginBottom: 24,
                        alignItems: 'center',
                        shadowColor: '#000',
                        shadowOffset: { width: 0, height: 2 },
                        shadowOpacity: 0.1,
                        shadowRadius: 8,
                        elevation: 3,
                    }}>
                        <ActivityIndicator size="large" color={COLORS.PRIMARY} />
                        <Text style={{ fontSize: 16, color: '#6b7280', marginTop: 16 }}>
                            Cargando médicos...
                        </Text>
                    </View>
                )}

                {/* Search Results Dropdown */}
                {showDropdown && filteredDoctors.length > 0 && !loading && (
                    <View style={{
                        backgroundColor: 'white',
                        borderRadius: 16,
                        maxHeight: 240,
                        shadowColor: '#000',
                        shadowOffset: { width: 0, height: 4 },
                        shadowOpacity: 0.15,
                        shadowRadius: 12,
                        elevation: 5,
                        marginBottom: 24,
                        borderWidth: 1,
                        borderColor: '#e5e7eb',
                    }}>
                        <ScrollView showsVerticalScrollIndicator={false}>
                            {filteredDoctors.map((doctor, index) => (
                                <TouchableOpacity
                                    key={`${doctor.IdRecurso}-${doctor.IdEspecialidad}-${doctor.IdServicio}-${doctor.IdSucursal}`}
                                    style={{
                                        paddingVertical: 16,
                                        paddingHorizontal: 20,
                                        borderBottomWidth: index === filteredDoctors.length - 1 ? 0 : 1,
                                        borderBottomColor: '#f3f4f6',
                                    }}
                                    onPress={() => selectDoctor(doctor)}
                                >
                                    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <View style={{ flex: 1 }}>
                                            <Text style={{ fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 4 }}>
                                                {doctor.Nombre}
                                            </Text>
                                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                                <Ionicons name="star-outline" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                                    {doctor.Especialidad}
                                                </Text>
                                            </View>
                                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                                <Ionicons name="location" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                                    {doctor.Sucursal}
                                                </Text>
                                            </View>
                                        </View>
                                        <Ionicons name="chevron-forward" size={16} color="#6b7280" />
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </ScrollView>
                    </View>
                )}

                {/* No Results Message */}
                {showDropdown && filteredDoctors.length === 0 && searchText.trim().length >= 4 && !loading && (
                    <View style={{
                        backgroundColor: 'white',
                        borderRadius: 16,
                        padding: 32,
                        marginBottom: 24,
                        alignItems: 'center',
                        shadowColor: '#000',
                        shadowOffset: { width: 0, height: 2 },
                        shadowOpacity: 0.1,
                        shadowRadius: 8,
                        elevation: 3,
                    }}>
                        <Ionicons name="search-outline" size={48} color="#d1d5db" />
                        <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, fontWeight: '500' }}>
                            No se encontraron resultados
                        </Text>
                        <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 4, textAlign: 'center' }}>
                            Intenta con diferentes palabras clave
                        </Text>
                    </View>
                )}

                {/* Selected Item Display */}
                {selectedDoctor && (
                    <View style={{
                        backgroundColor: 'white',
                        borderRadius: 16,
                        padding: 24,
                        marginBottom: 24,
                        borderWidth: 2,
                        borderColor: COLORS.PRIMARY,
                        shadowColor: COLORS.PRIMARY,
                        shadowOffset: { width: 0, height: 4 },
                        shadowOpacity: 0.1,
                        shadowRadius: 8,
                        elevation: 3,
                    }}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
                            <Ionicons name="checkmark-circle" size={24} color={COLORS.PRIMARY} style={{ marginRight: 8 }} />
                            <Text style={{ fontSize: 20, fontWeight: '700', color: '#111827' }}>
                                Medico seleccionado
                            </Text>
                        </View>
                        <View style={{
                            backgroundColor: '#f8fafc',
                            padding: 16,
                            borderRadius: 12,
                            marginBottom: 16,
                        }}>
                            <Text style={{ fontSize: 18, fontWeight: '600', color: '#111827', marginBottom: 6 }}>
                                {selectedDoctor.Nombre}
                            </Text>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <Ionicons name="star-outline" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                    {selectedDoctor.Especialidad}
                                </Text>
                            </View>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <Ionicons name="medical" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                    {selectedDoctor.Servicio}
                                </Text>
                            </View>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <Ionicons name="location" size={16} color="#6b7280" style={{ marginRight: 6 }} />
                                <Text style={{ fontSize: 15, color: '#6b7280' }}>
                                    {selectedDoctor.Sucursal}
                                </Text>
                            </View>
                        </View>

                        {/* Service Selection */}
                        <View style={{ marginBottom: 16 }}>
                            <Text style={{ fontSize: 16, fontWeight: '600', marginBottom: 12, color: '#111827' }}>
                                Tipo de turno
                            </Text>

                            {loadingServices ? (
                                <View style={{
                                    backgroundColor: 'white',
                                    borderRadius: 12,
                                    paddingHorizontal: 16,
                                    paddingVertical: 14,
                                    borderWidth: 1,
                                    borderColor: '#e5e7eb',
                                    flexDirection: 'row',
                                    alignItems: 'center',
                                }}>
                                    <ActivityIndicator size="small" color={COLORS.PRIMARY} style={{ marginRight: 10 }} />
                                    <Text style={{ fontSize: 16, color: '#6b7280' }}>
                                        Cargando tipos de turno...
                                    </Text>
                                </View>
                            ) : (
                                <TouchableOpacity
                                    style={{
                                        backgroundColor: 'white',
                                        borderRadius: 12,
                                        paddingHorizontal: 16,
                                        paddingVertical: 14,
                                        borderWidth: 1,
                                        borderColor: selectedService ? COLORS.PRIMARY : '#e5e7eb',
                                        flexDirection: 'row',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        shadowColor: '#000',
                                        shadowOffset: { width: 0, height: 1 },
                                        shadowOpacity: 0.05,
                                        shadowRadius: 2,
                                        elevation: 1,
                                    }}
                                    onPress={() => setShowServiceDropdown(!showServiceDropdown)}
                                >
                                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                        <Ionicons name="medical" size={18} color="#6b7280" style={{ marginRight: 10 }} />
                                        <Text style={{
                                            fontSize: 16,
                                            color: selectedService ? '#111827' : '#6b7280',
                                            fontWeight: selectedService ? '500' : '400'
                                        }}>
                                            {selectedService ? selectedService.name : 'Choose service type...'}
                                        </Text>
                                    </View>
                                    <Ionicons
                                        name={showServiceDropdown ? "chevron-up" : "chevron-down"}
                                        size={18}
                                        color="#6b7280"
                                    />
                                </TouchableOpacity>
                            )}

                            {/* Service Options Dropdown */}
                            {showServiceDropdown && serviceOptions.length > 0 && (
                                <View style={{
                                    backgroundColor: 'white',
                                    borderRadius: 12,
                                    marginTop: 8,
                                    shadowColor: '#000',
                                    shadowOffset: { width: 0, height: 4 },
                                    shadowOpacity: 0.15,
                                    shadowRadius: 8,
                                    elevation: 4,
                                    borderWidth: 1,
                                    borderColor: '#e5e7eb',
                                }}>
                                    {serviceOptions.map((service, index) => (
                                        <TouchableOpacity
                                            key={service.id}
                                            style={{
                                                paddingVertical: 14,
                                                paddingHorizontal: 16,
                                                borderBottomWidth: index === serviceOptions.length - 1 ? 0 : 1,
                                                borderBottomColor: '#f3f4f6',
                                            }}
                                            onPress={() => selectService(service)}
                                        >
                                            <Text style={{ fontSize: 16, fontWeight: '500', color: '#111827', marginBottom: 2 }}>
                                                {service.name}
                                            </Text>
                                        </TouchableOpacity>
                                    ))}
                                </View>
                            )}
                        </View>

                        {/* Timeframe Selection */}
                        <View style={{ marginBottom: 16 }}>
                            <Text style={{ fontSize: 16, fontWeight: '600', marginBottom: 12, color: '#111827' }}>
                                Buscar turnos dentro de
                            </Text>

                            <TouchableOpacity
                                style={{
                                    backgroundColor: 'white',
                                    borderRadius: 12,
                                    paddingHorizontal: 16,
                                    paddingVertical: 14,
                                    borderWidth: 1,
                                    borderColor: COLORS.PRIMARY,
                                    flexDirection: 'row',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    shadowColor: '#000',
                                    shadowOffset: { width: 0, height: 1 },
                                    shadowOpacity: 0.05,
                                    shadowRadius: 2,
                                    elevation: 1,
                                }}
                                onPress={() => setShowTimeframeDropdown(!showTimeframeDropdown)}
                            >
                                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                    <Ionicons name="time" size={18} color="#6b7280" style={{ marginRight: 10 }} />
                                    <Text style={{
                                        fontSize: 16,
                                        color: '#111827',
                                        fontWeight: '500'
                                    }}>
                                        {selectedTimeframe.label}
                                    </Text>
                                </View>
                                <Ionicons
                                    name={showTimeframeDropdown ? "chevron-up" : "chevron-down"}
                                    size={18}
                                    color="#6b7280"
                                />
                            </TouchableOpacity>

                            {/* Timeframe Options Dropdown */}
                            {showTimeframeDropdown && (
                                <View style={{
                                    backgroundColor: 'white',
                                    borderRadius: 12,
                                    marginTop: 8,
                                    maxHeight: 200,
                                    shadowColor: '#000',
                                    shadowOffset: { width: 0, height: 4 },
                                    shadowOpacity: 0.15,
                                    shadowRadius: 8,
                                    elevation: 4,
                                    borderWidth: 1,
                                    borderColor: '#e5e7eb',
                                    zIndex: 1000,
                                }}>
                                    <ScrollView
                                        showsVerticalScrollIndicator={false}
                                        nestedScrollEnabled={true}
                                    >
                                        {TIMEFRAME_OPTIONS.map((timeframe, index) => (
                                            <TouchableOpacity
                                                key={timeframe.value}
                                                style={{
                                                    paddingVertical: 14,
                                                    paddingHorizontal: 16,
                                                    borderBottomWidth: index === TIMEFRAME_OPTIONS.length - 1 ? 0 : 1,
                                                    borderBottomColor: '#f3f4f6',
                                                }}
                                                onPress={() => selectTimeframe(timeframe)}
                                            >
                                                <Text style={{
                                                    fontSize: 16,
                                                    fontWeight: '500',
                                                    color: selectedTimeframe.value === timeframe.value ? COLORS.PRIMARY : '#111827'
                                                }}>
                                                    {timeframe.label}
                                                </Text>
                                            </TouchableOpacity>
                                        ))}
                                    </ScrollView>
                                </View>
                            )}
                        </View>

                        {/* Add Button */}
                        <TouchableOpacity
                            style={{
                                backgroundColor: selectedService ? COLORS.PRIMARY : '#d1d5db',
                                paddingVertical: 14,
                                borderRadius: 12,
                                alignItems: 'center',
                                shadowColor: selectedService ? COLORS.PRIMARY : 'transparent',
                                shadowOffset: { width: 0, height: 4 },
                                shadowOpacity: selectedService ? 0.3 : 0,
                                shadowRadius: 8,
                                elevation: selectedService ? 4 : 0,
                            }}
                            onPress={handleAdd}
                            disabled={!selectedService}
                        >
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <Ionicons name="add" size={20} color="white" style={{ marginRight: 8 }} />
                                <Text style={{
                                    color: 'white',
                                    fontSize: 16,
                                    fontWeight: '600',
                                }}>
                                    {selectedService ? 'Agregar' : 'Seleccionar tipo de turno'}
                                </Text>
                            </View>
                        </TouchableOpacity>
                    </View>
                )}

            </ScrollView>
        </View>
    );
} 