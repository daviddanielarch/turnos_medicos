# Turnos Medicos - Sanatorio Allende Mobile App

A React Native mobile application for booking medical appointments at Sanatorio Allende. Built with Expo and integrated with a Django backend API.

## Features

- **Patient Management**: View and manage patient information
- **Appointment Search**: Search for available medical appointments
- **Best Appointments**: Find optimal appointment slots based on preferences
- **Push Notifications**: Receive notifications for appointment updates
- **Authentication**: Secure login with Auth0 integration
- **Offline Support**: Background task management for appointment monitoring

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator (for iOS development) or Android Studio (for Android development)
- Auth0 account (for authentication)

## Configuration

### API Host Configuration

The app connects to the Django backend API. Configure the API host in one of these ways:

1. **Environment Variable (Recommended)**: Create a `.env` file in the root directory:
   ```
   EXPO_PUBLIC_API_HOST=https://turnos-medicos.up.railway.app
   ```

2. **App Configuration**: Update the `app.json` file in the `extra.apiHost` field:
   ```json
   {
     "expo": {
       "extra": {
         "apiHost": "https://turnos-medicos.up.railway.app"
       }
     }
   }
   ```

3. **Default Fallback**: If neither is configured, it defaults to the production API

### Auth0 Authentication Setup

This app uses Auth0 for authentication. Follow the detailed setup guide in [AUTH_SETUP.md](./AUTH_SETUP.md) to configure:

- Auth0 tenant and application
- Mobile app configuration
- Redirect URIs and callback URLs
- Token storage and security

## Installation & Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure API host** (see Configuration section above)

3. **Set up Auth0 authentication** (see AUTH_SETUP.md)

4. **Start the development server**:
   ```bash
   npx expo start
   ```

## Development

### Available Scripts

- `npm start` - Start the Expo development server
- `npm run android` - Run on Android device/emulator
- `npm run ios` - Run on iOS simulator
- `npm run web` - Run in web browser
- `npm run lint` - Run ESLint

### Project Structure

```
app/
├── _layout.tsx          # Root layout and navigation
├── index.tsx            # Home screen
├── patients.tsx         # Patient management
├── search.tsx           # Appointment search
└── best-appointments.tsx # Best appointments finder

src/
├── components/          # Reusable UI components
├── config/             # Configuration files
├── constants/          # App constants
├── contexts/           # React contexts
└── hooks/              # Custom React hooks

services/
├── apiService.ts       # API communication
├── pushNotificationService.ts # Push notifications
└── secureStorage.ts    # Secure token storage
```

### Key Technologies

- **Expo SDK 53** - React Native development platform
- **Expo Router** - File-based routing
- **React Native Auth0** - Authentication
- **Expo Notifications** - Push notifications
- **Expo Secure Store** - Secure token storage
- **TypeScript** - Type safety

## Building for Production

### Android

1. **Configure EAS Build**:
   ```bash
   npx eas build:configure
   ```

2. **Build APK/AAB**:
   ```bash
   npx eas build --platform android
   ```

### iOS

1. **Configure EAS Build**:
   ```bash
   npx eas build:configure
   ```

2. **Build IPA**:
   ```bash
   npx eas build --platform ios
   ```

## Troubleshooting

### Common Issues

1. **Authentication errors**: Check Auth0 configuration in `AUTH_SETUP.md`
2. **API connection issues**: Verify API host configuration
3. **Push notification problems**: Ensure proper notification setup
4. **Build failures**: Check EAS configuration and credentials

### Debug Mode

Enable debug logging by adding console.log statements in the relevant service files.

## Contributing

1. Follow the existing code style and TypeScript conventions
2. Test on both iOS and Android before submitting changes
3. Update documentation for any new features or configuration changes

## License

This project is part of the Turnos Medicos system for Sanatorio Allende.
