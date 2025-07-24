import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { useEffect } from "react";
import backgroundService from "../services/backgroundService";
import { COLORS } from "./constants";

export default function RootLayout() {
  useEffect(() => {
    // Automatically start background service when app launches
    const initializeBackgroundService = async () => {
      try {
        console.log('[App] Initializing background service...');
        await backgroundService.startBackgroundCheck();
        console.log('[App] Background service initialized successfully');
      } catch (error) {
        console.error('[App] Error initializing background service:', error);
      }
    };

    initializeBackgroundService();
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
