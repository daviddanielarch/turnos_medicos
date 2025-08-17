import CustomHeader from "@/src/components/CustomHeader";
import { COLORS } from "@/src/constants/constants";
import { useAuth0Context } from "@/src/contexts/Auth0Context";
import { usePatientContext } from "@/src/contexts/PatientContext";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "@react-navigation/native";
import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, RefreshControl, ScrollView, Text, TouchableOpacity, View } from "react-native";
import apiService from "../services/apiService";

interface FindAppointments {
  id: number;
  name: string;
  location: string;
  especialidad: string;
  enabled: boolean;
  tipo_de_turno: string;
  desired_timeframe: string;
  doctor_id: number;
  tipo_de_turno_id: number;
}

export default function Index() {
  const [items, setItems] = useState<FindAppointments[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [updatingItems, setUpdatingItems] = useState<Set<number>>(new Set());
  const { isAuthenticated } = useAuth0Context();
  const { selectedPatient } = usePatientContext();

  // Fetch appointments when component mounts and user is authenticated
  useEffect(() => {
    if (isAuthenticated && selectedPatient) {
      fetchAppointments();
    }
  }, [isAuthenticated, selectedPatient]);

  // Refresh appointments when tab comes into focus and user is authenticated
  useFocusEffect(
    useCallback(() => {
      if (isAuthenticated && selectedPatient) {
        fetchAppointments();
      }
    }, [isAuthenticated, selectedPatient])
  );

  const fetchAppointments = async () => {
    if (!selectedPatient) {
      console.log('No patient selected');
      return;
    }

    if (!selectedPatient.id) {
      console.log('Selected patient has no ID:', selectedPatient);
      return;
    }

    console.log('Selected patient:', selectedPatient);
    console.log('Selected patient ID:', selectedPatient.id);

    setLoading(true);
    try {
      const response = await apiService.getFindAppointments(selectedPatient.id);

      if (response.success && response.data) {
        setItems(response.data.appointments);
      } else {
        console.error('Failed to fetch appointments:', response.error);
      }
    } catch (error) {
      console.error('Error fetching appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    if (isAuthenticated && selectedPatient) {
      await fetchAppointments();
    }
    setRefreshing(false);
  };

  const updateAppointmentStatus = async (appointmentId: number, active: boolean) => {
    try {
      const response = await apiService.updateFindAppointmentStatus(appointmentId, active);

      if (response.success) {
        console.log('Appointment status updated successfully');
        return true;
      } else {
        console.error('Failed to update appointment status:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Error updating appointment status:', error);
      return false;
    }
  };

  const toggleItem = async (id: number) => {
    const item = items.find(item => item.id === id);
    if (!item) return;

    const newEnabled = !item.enabled;

    // Optimistically update the UI
    setItems(items.map(item =>
      item.id === id ? { ...item, enabled: newEnabled } : item
    ));

    // Add to updating set
    setUpdatingItems(prev => new Set(prev).add(id));

    // Make API call
    const success = await updateAppointmentStatus(id, newEnabled);

    // Remove from updating set
    setUpdatingItems(prev => {
      const newSet = new Set(prev);
      newSet.delete(id);
      return newSet;
    });

    // If the API call failed, revert the UI change
    if (!success) {
      setItems(items.map(item =>
        item.id === id ? { ...item, enabled: !newEnabled } : item
      ));
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
        <CustomHeader title="Turnos activados" />
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={COLORS.PRIMARY} />
          <Text style={{ fontSize: 16, color: '#6b7280', marginTop: 16 }}>
            Cargando turnos...
          </Text>
        </View>
      </View>
    );
  }

  if (!selectedPatient) {
    return (
      <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
        <CustomHeader title="Turnos activados" />
        <View style={{
          backgroundColor: 'white',
          padding: 32,
          marginTop: 8,
          marginHorizontal: 16,
          borderRadius: 12,
          alignItems: 'center',
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 1 },
          shadowOpacity: 0.05,
          shadowRadius: 4,
          elevation: 2,
        }}>
          <Ionicons name="person-outline" size={48} color="#d1d5db" />
          <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, fontWeight: '500' }}>
            No hay paciente seleccionado
          </Text>
          <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 4, textAlign: 'center' }}>
            Ve a la pestaña "Pacientes" para seleccionar un paciente
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      <CustomHeader title="Turnos activados" />

      {/* Items List */}
      <ScrollView
        style={{ flex: 1, paddingHorizontal: 16, paddingVertical: 16 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {items.length === 0 ? (
          <View style={{
            backgroundColor: 'white',
            padding: 32,
            marginTop: 8,
            borderRadius: 12,
            alignItems: 'center',
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.05,
            shadowRadius: 4,
            elevation: 2,
          }}>
            <Ionicons name="calendar-outline" size={48} color="#d1d5db" />
            <Text style={{ fontSize: 18, color: '#6b7280', marginTop: 16, fontWeight: '500' }}>
              No hay turnos configurados
            </Text>
            <Text style={{ fontSize: 14, color: '#9ca3af', marginTop: 4, textAlign: 'center' }}>
              Ve a la pestaña "Buscar" para agregar turnos
            </Text>
          </View>
        ) : (
          items.map((item, index) => {
            const isUpdating = updatingItems.has(item.id);

            return (
              <View key={item.id} style={{
                flexDirection: 'row',
                backgroundColor: 'white',
                paddingVertical: 20,
                paddingHorizontal: 20,
                marginTop: 8,
                borderRadius: 12,
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 1 },
                shadowOpacity: 0.05,
                shadowRadius: 4,
                elevation: 2,
                borderLeftWidth: 4,
                borderLeftColor: item.enabled ? COLORS.PRIMARY : '#e5e7eb',
                opacity: isUpdating ? 0.7 : 1,
              }}>
                <View style={{ flex: 2, justifyContent: 'center' }}>
                  <Text style={{ fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 4 }}>
                    {item.name}
                  </Text>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 2 }}>
                    <Ionicons name="star-outline" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                    <Text style={{ fontSize: 14, color: '#6b7280' }}>
                      {item.especialidad} ({item.tipo_de_turno})
                    </Text>
                  </View>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 2 }}>
                    <Ionicons name="location" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                    <Text style={{ fontSize: 14, color: '#6b7280' }}>
                      {item.location}
                    </Text>
                  </View>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 2 }}>
                    <Ionicons name="time" size={14} color="#6b7280" style={{ marginRight: 4 }} />
                    <Text style={{ fontSize: 14, color: '#6b7280' }}>
                      {item.desired_timeframe === 'anytime' ? 'Cualquier momento' :
                        item.desired_timeframe === '1 week' ? '1 semana' :
                          item.desired_timeframe === '2 weeks' ? '2 semanas' :
                            item.desired_timeframe === '3 weeks' ? '3 semanas' : item.desired_timeframe}
                    </Text>
                  </View>
                </View>
                <TouchableOpacity
                  style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}
                  onPress={() => toggleItem(item.id)}
                  disabled={isUpdating}
                >
                  {isUpdating ? (
                    <ActivityIndicator size="small" color={COLORS.PRIMARY} />
                  ) : (
                    <View style={{
                      width: 28,
                      height: 28,
                      borderRadius: 14,
                      borderWidth: 2,
                      borderColor: item.enabled ? COLORS.PRIMARY : '#d1d5db',
                      backgroundColor: item.enabled ? COLORS.PRIMARY : 'transparent',
                      justifyContent: 'center',
                      alignItems: 'center',
                      shadowColor: item.enabled ? COLORS.PRIMARY : 'transparent',
                      shadowOffset: { width: 0, height: 2 },
                      shadowOpacity: 0.2,
                      shadowRadius: 4,
                      elevation: item.enabled ? 3 : 0,
                    }}>
                      {item.enabled && (
                        <Ionicons name="checkmark" size={16} color="white" />
                      )}
                    </View>
                  )}
                </TouchableOpacity>
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}
