import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { COLORS } from "./constants";

interface Item {
  id: number;
  name: string;
  location: string;
  especialidad: string;
  enabled: boolean;
}

export default function Index() {
  const [items, setItems] = useState<Item[]>([
    { id: 1, name: "BARRERA ROSANA FABIANA", especialidad: "Alergia", location: "Cerro", enabled: true },
    { id: 2, name: "BARRERA ROSANA FABIANA", especialidad: "Alergia", location: "Nueva Cba", enabled: false },
  ]);

  const toggleItem = (id: number) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, enabled: !item.enabled } : item
    ));
  };

  const handleSave = () => {
    console.log('Saving items:', items);
  };

  return (
    <View style={{ flex: 1, paddingTop: 50, backgroundColor: '#f8fafc' }}>

      {/* Items List */}
      <ScrollView style={{ flex: 1, paddingHorizontal: 16 }} showsVerticalScrollIndicator={false}>
        {items.map((item, index) => (
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
        ))}

      </ScrollView>

      {/* Save Button */}
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
            backgroundColor: COLORS.PRIMARY,
            paddingVertical: 16,
            borderRadius: 12,
            alignItems: 'center',
            shadowColor: '#667eea',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.3,
            shadowRadius: 8,
            elevation: 4,
          }}
          onPress={handleSave}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={{
              color: 'white',
              fontSize: 18,
              fontWeight: '600',
            }}>
              Actualizar
            </Text>
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
}
