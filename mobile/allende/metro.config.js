const { getDefaultConfig } = require('expo/metro-config');
const fs = require('fs');
const path = require('path');

// Create google-services.json from environment variable if it doesn't exist
if (process.env.GOOGLE_SERVICES_JSON && !fs.existsSync(path.join(__dirname, 'google-services.json'))) {
    try {
        fs.writeFileSync(path.join(__dirname, 'google-services.json'), process.env.GOOGLE_SERVICES_JSON);
        console.log('Created google-services.json from environment variable');
    } catch (error) {
        console.error('Failed to create google-services.json:', error);
    }
}

// Create allende-mobile-app-57c0658681aa.json from environment variable if it doesn't exist
if (process.env.MOBILE_APP_SERVICE_ACCOUNT_JSON && !fs.existsSync(path.join(__dirname, 'allende-mobile-app-57c0658681aa.json'))) {
    try {
        fs.writeFileSync(path.join(__dirname, 'allende-mobile-app-57c0658681aa.json'), process.env.MOBILE_APP_SERVICE_ACCOUNT_JSON);
        console.log('Created allende-mobile-app-57c0658681aa.json from environment variable');
    } catch (error) {
        console.error('Failed to create allende-mobile-app-57c0658681aa.json:', error);
    }
}

const config = getDefaultConfig(__dirname);

module.exports = config; 