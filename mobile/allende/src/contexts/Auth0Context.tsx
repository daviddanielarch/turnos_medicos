import React, { createContext, ReactNode, useContext, useEffect } from 'react';
import { Auth0Provider, Credentials, useAuth0 } from 'react-native-auth0';
import apiService from '../../services/apiService';
import { AUTH0_CONFIG } from '../config/auth0';

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
    console.log('[Auth0AppProvider] Initializing Auth0 provider...');
    return (
        <Auth0Provider
            domain={AUTH0_CONFIG.domain}
            clientId={AUTH0_CONFIG.clientId}
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
    const { authorize, clearSession, getCredentials, user, error } = useAuth0();

    const isAuthenticated = !!user;

    console.log('[Auth0ContextProvider] State:', {
        isAuthenticated,
        hasUser: !!user,
        hasError: !!error,
        error: error?.message
    });

    // Set up the API service with the credentials getter
    useEffect(() => {
        console.log('[Auth0ContextProvider] Setting up API service credentials getter...');
        apiService.setCredentialsGetter(getCredentials);
    }, [getCredentials]);

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