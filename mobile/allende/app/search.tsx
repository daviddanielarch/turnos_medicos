import CustomHeader from "@/src/components/CustomHeader";
import { COLORS } from "@/src/constants/constants";
import { useAuth0Context } from "@/src/contexts/Auth0Context";
import { usePatientContext } from "@/src/contexts/PatientContext";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, Text, TextInput, TouchableOpacity, View } from "react-native";
import apiService from "../services/apiService";

interface Item {
    id: number;
    name: string;
    location: string;
    especialidad: string;
}

interface ServiceOption {
    id: string;
    name: string;
    description: string;
    id_tipo_turno: number;
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
    const [selectedItem, setSelectedItem] = useState<Item | null>(null);
    const [selectedService, setSelectedService] = useState<ServiceOption | null>(null);
    const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeOption>(TIMEFRAME_OPTIONS[0]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [showServiceDropdown, setShowServiceDropdown] = useState(false);
    const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false);
    const [filteredItems, setFilteredItems] = useState<Item[]>([]);
    const [allItems, setAllItems] = useState<Item[]>([]);
    const [serviceOptions, setServiceOptions] = useState<ServiceOption[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingServices, setLoadingServices] = useState(false);
    const { isAuthenticated } = useAuth0Context();
    const { selectedPatient } = usePatientContext();

    useEffect(() => {
        if (isAuthenticated) {
            fetchDoctors();
        }
    }, [isAuthenticated]);

    const fetchDoctors = async () => {
        setLoading(true);
        try {
            const response = await apiService.getDoctors();

            if (response.success && response.data) {
                setAllItems((response.data as any).doctors);
            } else {
                console.error('Failed to fetch doctors:', response.error);
            }
        } catch (error) {
            console.error('Error fetching doctors:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchAppointmentTypes = async (doctorId: number) => {
        setLoadingServices(true);
        try {
            const response = await apiService.getAppointmentTypes(doctorId);

            if (response.success && response.data) {
                setServiceOptions((response.data as any).appointment_types);
            } else {
                console.error('Failed to fetch appointment types:', response.error);
            }
        } catch (error) {
            console.error('Error fetching appointment types:', error);
        } finally {
            setLoadingServices(false);
        }
    };

    const handleSearch = (text: string) => {
        setSearchText(text);
        if (text.trim() === "") {
            setFilteredItems([]);
        } else {
            const filtered = allItems.filter(item =>
                item.name.toLowerCase().includes(text.toLowerCase()) ||
                item.location.toLowerCase().includes(text.toLowerCase()) ||
                item.especialidad.toLowerCase().includes(text.toLowerCase())
            );
            setFilteredItems(filtered);
        }
    };

    const selectItem = (item: Item) => {
        setSelectedItem(item);
        setSearchText(item.name);
        setFilteredItems([]);
        setShowDropdown(false);
        setSelectedService(null);
        fetchAppointmentTypes(item.id);
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
        setSelectedItem(null);
        setSelectedService(null);
        setSelectedTimeframe(TIMEFRAME_OPTIONS[0]);
        setSearchText("");
        setFilteredItems([]);
        setServiceOptions([]);
    };

    const handleAdd = async () => {
        if (selectedItem && selectedService) {
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
                    doctor_id: selectedItem.id,
                    appointment_type_id: parseInt(selectedService.id),
                    patient_id: selectedPatient.id,
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
            <View style={{ padding: 20 }}>
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
                        onFocus={() => setShowDropdown(true)}
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
                {showDropdown && filteredItems.length > 0 && !loading && (
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
                            {filteredItems.map((item, index) => (
                                <TouchableOpacity
                                    key={item.id}
                                    style={{
                                        paddingVertical: 16,
                                        paddingHorizontal: 20,
                                        borderBottomWidth: index === filteredItems.length - 1 ? 0 : 1,
                                        borderBottomColor: '#f3f4f6',
                                    }}
                                    onPress={() => selectItem(item)}
                                >
                                    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <View style={{ flex: 1 }}>
                                            <Text style={{ fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 4 }}>
                                                {item.name}
                                            </Text>
                                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                                <Ionicons name="star-outline" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                                    {item.especialidad}
                                                </Text>
                                            </View>
                                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                                <Ionicons name="location" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                                    {item.location}
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
                {showDropdown && filteredItems.length === 0 && searchText.trim() !== "" && !loading && (
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
                {selectedItem && (
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
                                {selectedItem.name}
                            </Text>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <Ionicons name="star-outline" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                                <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                    {selectedItem.especialidad}
                                </Text>
                            </View>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <Ionicons name="location" size={16} color="#6b7280" style={{ marginRight: 6 }} />
                                <Text style={{ fontSize: 15, color: '#6b7280' }}>
                                    {selectedItem.location}
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
                                            <Text style={{ fontSize: 14, color: '#6b7280' }}>
                                                {service.description}
                                            </Text>
                                        </TouchableOpacity>
                                    ))}
                                </View>
                            )}
                        </View>

                        {/* Timeframe Selection */}
                        <View style={{ marginBottom: 16 }}>
                            <Text style={{ fontSize: 16, fontWeight: '600', marginBottom: 12, color: '#111827' }}>
                                Marco de tiempo deseado
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
                                    shadowColor: '#000',
                                    shadowOffset: { width: 0, height: 4 },
                                    shadowOpacity: 0.15,
                                    shadowRadius: 8,
                                    elevation: 4,
                                    borderWidth: 1,
                                    borderColor: '#e5e7eb',
                                }}>
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


            </View>
        </View>
    );
} 