# Welcome to your Expo app 👋

This is an [Expo](https://expo.dev) project created with [`create-expo-app`](https://www.npmjs.com/package/create-expo-app).

## Configuration

### API Host Configuration

The app needs to know where your Django backend API is running. You can configure this in several ways:

1. **Environment Variable (Recommended)**: Create a `.env` file in the root directory:
   ```
   EXPO_PUBLIC_API_HOST=http://localhost:8000
   ```

2. **App Configuration**: Update the `app.json` file in the `extra.apiHost` field:
   ```json
   {
     "expo": {
       "extra": {
         "apiHost": "http://localhost:8000"
       }
     }
   }
   ```

3. **Default Fallback**: If neither is configured, it defaults to `http://localhost:8000`

### Environment Variables

- `EXPO_PUBLIC_API_HOST`: The base URL for your Django API backend
  - Development: `http://localhost:8000`
  - Production: `https://your-api-domain.com`

## Get started

1. Install dependencies

   ```bash
   npm install
   ```

2. Configure your API host (see Configuration section above)

3. Start the app

   ```bash
   npx expo start
   ```

In the output, you'll find options to open the app in a

- [development build](https://docs.expo.dev/develop/development-builds/introduction/)
- [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
- [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/)
- [Expo Go](https://expo.dev/go), a limited sandbox for trying out app development with Expo

You can start developing by editing the files inside the **app** directory. This project uses [file-based routing](https://docs.expo.dev/router/introduction).

## Get a fresh project

When you're ready, run:

```bash
npm run reset-project
```

This command will move the starter code to the **app-example** directory and create a blank **app** directory where you can start developing.

## Learn more

To learn more about developing your project with Expo, look at the following resources:

- [Expo documentation](https://docs.expo.dev/): Learn fundamentals, or go into advanced topics with our [guides](https://docs.expo.dev/guides).
- [Learn Expo tutorial](https://docs.expo.dev/tutorial/introduction/): Follow a step-by-step tutorial where you'll create a project that runs on Android, iOS, and the web.

## Join the community

Join our community of developers creating universal apps.

- [Expo on GitHub](https://github.com/expo/expo): View our open source platform and contribute.
- [Discord community](https://chat.expo.dev): Chat with Expo users and ask questions.
