// Auth0 Configuration
export const AUTH0_CONFIG = {
    domain: 'daviddanielarch.auth0.com',
    clientId: '8IYHXBrV3fqEEfFsupCZNfXc8ikTS8CB',
    audience: 'https://daviddanielarch.auth0.com/api/v2/',
    scope: 'openid profile email',
} as const;

// Auth0 authorization parameters
export const AUTH0_AUTHORIZE_PARAMS = {
    audience: AUTH0_CONFIG.audience,
    scope: AUTH0_CONFIG.scope,
} as const; 