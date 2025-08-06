import { COLORS } from "@/src/constants/constants";
import { Auth0AppProvider, Auth0ContextProvider, useAuth0Context } from "@/src/contexts/Auth0Context";
import { PatientProvider } from "@/src/contexts/PatientContext";
import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { useEffect } from "react";
import { StyleSheet } from "react-native";
import LoginScreen from "../auth/login";
import pushNotificationService from "../services/pushNotificationService";
import { UpdateService } from "../services/updateService";

function AppContent() {
  const { isAuthenticated, user, error, getCredentials } = useAuth0Context();

  useEffect(() => {
    // Check for updates when app starts
    const checkForUpdates = async () => {
      try {
        console.log('[App] Checking for updates...');
        const hasUpdate = await UpdateService.checkForUpdates();

        if (hasUpdate) {
          console.log('[App] Update available, fetching...');
          const updated = await UpdateService.fetchUpdate();
          if (updated) {
            console.log('[App] Update applied successfully');
          } else {
            console.log('[App] Failed to apply update');
          }
        } else {
          console.log('[App] No updates available');
        }
      } catch (error) {
        console.error('[App] Error checking for updates:', error);
      }
    };

    checkForUpdates();
  }, []);

  useEffect(() => {
    // Only set up push notifications if user is authenticated
    if (!isAuthenticated) {
      console.log('[App] User not authenticated, skipping push notification setup');
      return;
    }

    // Set up push notifications for backend notifications
    const setupPushNotifications = async () => {
      try {
        console.log('[App] Setting up push notifications for authenticated user...');

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
  }, [isAuthenticated, user, error, getCredentials]);


  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  // Show main app with tabs if authenticated
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
      <Tabs.Screen
        name="patients"
        options={{
          title: "Pacientes",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

export default function RootLayout() {
  return (
    <Auth0AppProvider>
      <Auth0ContextProvider>
        <PatientProvider>
          <AppContent />
        </PatientProvider>
      </Auth0ContextProvider>
    </Auth0AppProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
});
