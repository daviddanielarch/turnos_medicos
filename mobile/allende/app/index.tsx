import { API_ENDPOINTS } from "@/src/config/config";
import { COLORS } from "@/src/constants/constants";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "@react-navigation/native";
import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Alert, RefreshControl, ScrollView, Text, TouchableOpacity, View } from "react-native";

interface Item {
  id: number;
  name: string;
  location: string;
  especialidad: string;
  enabled: boolean;
  tipo_de_turno: string;
}

export default function Index() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch appointments when component mounts
  useEffect(() => {
    fetchAppointments();
  }, []);

  // Refresh appointments when tab comes into focus
  useFocusEffect(
    useCallback(() => {
      fetchAppointments();
    }, [])
  );

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.FIND_APPOINTMENTS);
      const data = await response.json();

      if (data.success) {
        setItems(data.appointments);
      } else {
        console.error('Failed to fetch appointments:', data.error);
        Alert.alert('Error', 'Failed to load appointments');
      }
    } catch (error) {
      console.error('Error fetching appointments:', error);
      Alert.alert('Error', 'Network error while loading appointments');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchAppointments();
    setRefreshing(false);
  };

  const toggleItem = (id: number) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, enabled: !item.enabled } : item
    ));
  };

  const updateAppointmentStatus = async (appointmentId: number, active: boolean) => {
    try {
      const response = await fetch(API_ENDPOINTS.FIND_APPOINTMENTS, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          appointment_id: appointmentId,
          active: active
        }),
      });

      const data = await response.json();

      if (data.success) {
        console.log('Appointment status updated successfully');
      } else {
        console.error('Failed to update appointment status:', data.error);
        Alert.alert('Error', 'Failed to update appointment status');
      }
    } catch (error) {
      console.error('Error updating appointment status:', error);
      Alert.alert('Error', 'Network error while updating appointment status');
    }
  };

  const handleSave = async () => {
    setSaving(true);

    // Update all changed items
    const updatePromises = items.map(item =>
      updateAppointmentStatus(item.id, item.enabled)
    );

    try {
      await Promise.all(updatePromises);
      Alert.alert('Success', 'Appointments updated successfully');
      // Refresh the data
      fetchAppointments();
    } catch (error) {
      console.error('Error saving appointments:', error);
      Alert.alert('Error', 'Failed to save appointments');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, paddingTop: 50, backgroundColor: '#f8fafc', justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={COLORS.PRIMARY} />
        <Text style={{ fontSize: 16, color: '#6b7280', marginTop: 16 }}>
          Cargando turnos...
        </Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, paddingTop: 50, backgroundColor: '#f8fafc' }}>

      {/* Header */}
      <View style={{ paddingHorizontal: 20, paddingBottom: 16 }}>
        <Text style={{ fontSize: 24, fontWeight: '700', color: '#111827', marginBottom: 4 }}>
          Turnos activados
        </Text>
        <Text style={{ fontSize: 16, color: '#6b7280' }}>
          {items.length} turno{items.length !== 1 ? 's' : ''} configurado{items.length !== 1 ? 's' : ''}
        </Text>
      </View>

      {/* Items List */}
      <ScrollView
        style={{ flex: 1, paddingHorizontal: 16 }}
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
          items.map((item, index) => (
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
              </View>
              <TouchableOpacity
                style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}
                onPress={() => toggleItem(item.id)}
              >
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
              </TouchableOpacity>
            </View>
          ))
        )}
      </ScrollView>

      {/* Save Button */}
      {items.length > 0 && (
        <View style={{
          backgroundColor: 'white',
          paddingHorizontal: 20,
          paddingVertical: 20,
          paddingBottom: 30,
          borderTopWidth: 1,
          borderTopColor: '#e5e7eb',
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.1,
          shadowRadius: 8,
          elevation: 5,
        }}>
          <TouchableOpacity
            style={{
              backgroundColor: saving ? '#d1d5db' : COLORS.PRIMARY,
              paddingVertical: 16,
              borderRadius: 12,
              alignItems: 'center',
              shadowColor: saving ? 'transparent' : '#667eea',
              shadowOffset: { width: 0, height: 4 },
              shadowOpacity: saving ? 0 : 0.3,
              shadowRadius: 8,
              elevation: saving ? 0 : 4,
            }}
            onPress={handleSave}
            disabled={saving}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              {saving && (
                <ActivityIndicator size="small" color="white" style={{ marginRight: 8 }} />
              )}
              <Text style={{
                color: 'white',
                fontSize: 18,
                fontWeight: '600',
              }}>
                {saving ? 'Actualizando...' : 'Actualizar'}
              </Text>
            </View>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}
