import { COLORS } from "@/src/constants/constants";
import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { useEffect } from "react";
import pushNotificationService from "../services/pushNotificationService";

export default function RootLayout() {
  useEffect(() => {
    // Set up push notifications for backend notifications
    const setupPushNotifications = async () => {
      try {
        console.log('[App] Setting up push notifications...');

        // Set up notification handler
        pushNotificationService.setNotificationHandler();

        // Request permissions and register with backend
        const hasPermission = await pushNotificationService.requestPermissions();

        if (hasPermission) {
          // Register device with backend
          const registered = await pushNotificationService.registerDeviceWithBackend();
          if (registered) {
            console.log('[App] Device registered successfully with backend');
          } else {
            console.log('[App] Failed to register device with backend');
          }
        }

        console.log('[App] Push notifications setup completed');
      } catch (error) {
        console.error('[App] Error setting up push notifications:', error);
      }
    };

    setupPushNotifications();
  }, []);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: COLORS.PRIMARY,
        tabBarInactiveTintColor: '#666',
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Turnos activados",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="list" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: "Buscar",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="search" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="best-appointments"
        options={{
          title: "Mejores turnos",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="calendar" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
