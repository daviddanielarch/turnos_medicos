import { ConfigContext, ExpoConfig } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
    ...config,
    name: "allende",
    slug: "allende",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    scheme: "allende",
    userInterfaceStyle: "automatic",
    newArchEnabled: true,
    ios: {
        supportsTablet: true,
        infoPlist: {
            UIBackgroundModes: [
                "background-processing"
            ]
        },
        bundleIdentifier: "com.daviddanielarch.turnos-medicos"
    },
    android: {
        adaptiveIcon: {
            foregroundImage: "./assets/images/adaptive-icon.png",
            backgroundColor: "#ffffff"
        },
        edgeToEdgeEnabled: true,
        package: "com.daviddanielarch.turnos_medicos",
        googleServicesFile: process.env.GOOGLE_SERVICES_JSON ? "./google-services.json" : "./google-services.json",
        permissions: [
            "RECEIVE_BOOT_COMPLETED",
            "WAKE_LOCK",
            "VIBRATE",
            "android.permission.RECEIVE_BOOT_COMPLETED",
            "android.permission.WAKE_LOCK"
        ]
    },
    web: {
        bundler: "metro",
        output: "static",
        favicon: "./assets/images/favicon.png"
    },
    plugins: [
        "expo-router",
        [
            "expo-splash-screen",
            {
                "image": "./assets/images/splash-icon.png",
                "imageWidth": 200,
                "resizeMode": "contain",
                "backgroundColor": "#ffffff"
            }
        ],
        [
            "expo-notifications",
            {
                "icon": "./assets/images/notification-icon.png",
                "color": "#ffffff"
            }
        ]
    ],
    experiments: {
        typedRoutes: true
    },
    extra: {
        router: {},
        eas: {
            projectId: "92a909fc-8725-4e6c-a922-3f53e42399e0"
        },
        apiHost: "https://turnos-medicos.up.railway.app"
    },
    owner: "daviddanielarch"
}); 