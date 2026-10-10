// Web implementation of the Auth0 context. react-native-auth0 v4 only works on
// native, so on web we use @auth0/auth0-react while exposing the same API.
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import React, { createContext, ReactNode, useCallback, useContext, useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import apiService from '../../services/apiService';
import { AUTH0_CONFIG } from '../config/auth0';
import { COLORS } from '../constants/constants';

interface Credentials {
    accessToken?: string;
}

interface Auth0ContextType {
    isAuthenticated: boolean;
    user: any;
    error: any;
    authorize: (parameters?: any, options?: any) => Promise<Credentials | undefined>;
    clearSession: () => Promise<void>;
    getCredentials: () => Promise<Credentials | undefined>;
}

const Auth0Context = createContext<Auth0ContextType | undefined>(undefined);

interface Auth0ProviderProps {
    children: ReactNode;
}

export function Auth0AppProvider({ children }: Auth0ProviderProps) {
    return (
        <Auth0Provider
            domain={AUTH0_CONFIG.domain}
            clientId={AUTH0_CONFIG.webClientId}
            authorizationParams={{
                redirect_uri: window.location.origin,
                audience: AUTH0_CONFIG.audience,
                scope: AUTH0_CONFIG.scope,
            }}
            // Keep the session across page reloads (Safari blocks the iframe-based silent auth)
            cacheLocation="localstorage"
            useRefreshTokens
            useRefreshTokensFallback
        >
            {children}
        </Auth0Provider>
    );
}

export function useAuth0Context(): Auth0ContextType {
    const context = useContext(Auth0Context);
    if (context === undefined) {
        throw new Error('useAuth0Context must be used within an Auth0AppProvider');
    }
    return context;
}

export function Auth0ContextProvider({ children }: Auth0ProviderProps) {
    const { isLoading, isAuthenticated, user, error, loginWithRedirect, logout, getAccessTokenSilently } = useAuth0();

    const authorize = useCallback(async (parameters?: any) => {
        await loginWithRedirect({ authorizationParams: parameters });
        // The browser navigates away to Auth0; credentials are available after the redirect back.
        return undefined;
    }, [loginWithRedirect]);

    const clearSession = useCallback(async () => {
        await logout({ logoutParams: { returnTo: window.location.origin } });
    }, [logout]);

    const getCredentials = useCallback(async () => {
        const accessToken = await getAccessTokenSilently();
        return { accessToken };
    }, [getAccessTokenSilently]);

    useEffect(() => {
        apiService.setCredentialsGetter(getCredentials);
    }, [getCredentials]);

    if (isLoading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
                <ActivityIndicator size="large" color={COLORS.PRIMARY} />
            </View>
        );
    }

    const value: Auth0ContextType = {
        isAuthenticated,
        user,
        error,
        authorize,
        clearSession,
        getCredentials,
    };

    return (
        <Auth0Context.Provider value={value}>
            {children}
        </Auth0Context.Provider>
    );
}
