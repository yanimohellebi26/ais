export const DATE_FORMATS = {
    DATE_ONLY: /^\d{4}-\d{2}-\d{2}$/,
    DATE_TIME: /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/
} as const;

export const isValidDateFormat = (value: string): boolean => {
    if (!value.trim()) return true;
    return DATE_FORMATS.DATE_ONLY.test(value) || DATE_FORMATS.DATE_TIME.test(value);
};

export const formatDateTime = (dateTime: string): string => {
    try {
        const date = new Date(dateTime);
        return date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateTime;
    }
};