import { Alert, AlertButton, Platform } from 'react-native';

/**
 * Cross-platform Alert.alert. react-native-web's Alert is a no-op, so on web we
 * fall back to window.alert / window.confirm.
 */
export function showAlert(title: string, message?: string, buttons?: AlertButton[]) {
    if (Platform.OS !== 'web') {
        Alert.alert(title, message, buttons);
        return;
    }

    const text = [title, message].filter(Boolean).join('\n\n');

    if (!buttons || buttons.length <= 1) {
        window.alert(text);
        buttons?.[0]?.onPress?.();
        return;
    }

    const cancelButton = buttons.find((button) => button.style === 'cancel');
    const confirmButton = buttons.find((button) => button !== cancelButton);

    if (window.confirm(text)) {
        confirmButton?.onPress?.();
    } else {
        cancelButton?.onPress?.();
    }
}
