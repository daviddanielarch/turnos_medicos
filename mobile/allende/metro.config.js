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

// Create service account key file from environment variable if it doesn't exist
if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY && !fs.existsSync(path.join(__dirname, 'allende-mobile-app-57c0658681aa.json'))) {
    try {
        fs.writeFileSync(path.join(__dirname, 'allende-mobile-app-57c0658681aa.json'), process.env.GOOGLE_SERVICE_ACCOUNT_KEY);
        console.log('Created allende-mobile-app-57c0658681aa.json from environment variable');
    } catch (error) {
        console.error('Failed to create service account key file:', error);
    }
}

const config = getDefaultConfig(__dirname);

module.exports = config; 