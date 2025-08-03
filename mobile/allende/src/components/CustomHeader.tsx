import { COLORS } from '@/src/constants/constants';
import { useAuth0Context } from '@/src/contexts/Auth0Context';
import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

interface CustomHeaderProps {
    title?: string;
    showBackButton?: boolean;
    onBackPress?: () => void;
    showUserInfo?: boolean;
    showLogoutButton?: boolean;
}

export default function CustomHeader({
    title,
    showBackButton = false,
    onBackPress,
    showUserInfo = true,
    showLogoutButton = true
}: CustomHeaderProps) {
    const { user, clearSession } = useAuth0Context();
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    const getUserDisplayName = () => {
        if (!user) return 'User';

        // Try different possible name fields
        return user.name || user.nickname || user.email?.split('@')[0] || 'User';
    };

    const handleLogout = async () => {
        Alert.alert(
            'Cerrar Sesión',
            '¿Estás seguro de que quieres cerrar sesión?',
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Cerrar Sesión',
                    style: 'destructive',
                    onPress: async () => {
                        setIsLoggingOut(true);
                        try {
                            await clearSession();
                        } catch (error) {
                            console.error('Logout error:', error);
                            Alert.alert(
                                'Error de Cierre de Sesión',
                                'Ocurrió un error durante el cierre de sesión. Por favor, inténtalo de nuevo.',
                                [{ text: 'OK' }]
                            );
                        } finally {
                            setIsLoggingOut(false);
                        }
                    },
                },
            ]
        );
    };

    return (
        <View style={styles.header}>
            <View style={styles.headerContent}>
                {showBackButton && (
                    <TouchableOpacity
                        style={styles.backButton}
                        onPress={onBackPress}
                    >
                        <Ionicons name="arrow-back" size={24} color={COLORS.PRIMARY} />
                    </TouchableOpacity>
                )}

                <View style={styles.titleContainer}>
                    {title && (
                        <Text style={styles.title}>{title}</Text>
                    )}
                    {showUserInfo && (
                        <Text style={styles.userName}>{getUserDisplayName()}</Text>
                    )}
                </View>

                {showLogoutButton && (
                    <TouchableOpacity
                        style={[styles.logoutButton, isLoggingOut && styles.logoutButtonDisabled]}
                        onPress={handleLogout}
                        disabled={isLoggingOut}
                    >
                        {isLoggingOut ? (
                            <ActivityIndicator size="small" color="white" />
                        ) : (
                            <Ionicons name="log-out-outline" size={20} color="white" />
                        )}
                    </TouchableOpacity>
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    header: {
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        paddingTop: 50, // Account for status bar
        paddingBottom: 12,
        paddingHorizontal: 16,
    },
    headerContent: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    backButton: {
        padding: 8,
        marginRight: 12,
    },
    titleContainer: {
        flex: 1,
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 2,
    },
    userName: {
        fontSize: 14,
        color: '#666',
        fontWeight: '500',
    },
    logoutButton: {
        backgroundColor: '#dc3545',
        padding: 8,
        borderRadius: 6,
        marginLeft: 12,
    },
    logoutButtonDisabled: {
        opacity: 0.7,
    },
}); 