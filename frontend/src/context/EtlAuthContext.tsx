import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

type EtlAuthContextType = {
    apiKey: string | null;
    setApiKey: (key: string) => void;
    clearApiKey: () => void;
    isAuthenticated: boolean;
};

const EtlAuthContext = createContext<EtlAuthContextType | undefined>(undefined);

export const EtlAuthProvider = ({ children }: { children: ReactNode }) => {
    const [apiKey, setApiKeyState] = useState<string | null>(null);

    useEffect(() => {
        const storedKey = localStorage.getItem("etl_api_key");
        if (storedKey) setApiKeyState(storedKey);
    }, []);

    const setApiKey = (key: string) => {
        localStorage.setItem("etl_api_key", key);
        setApiKeyState(key);
    };

    const clearApiKey = () => {
        localStorage.removeItem("etl_api_key");
        setApiKeyState(null);
    };

    const isAuthenticated = !!apiKey;

    return (
        <EtlAuthContext.Provider value={{ apiKey, setApiKey, clearApiKey, isAuthenticated }}>
            {children}
        </EtlAuthContext.Provider>
    );
};

export const useEtlAuth = () => {
    const context = useContext(EtlAuthContext);
    if (!context) throw new Error("useEtlAuth must be used within an EtlAuthProvider");
    return context;
};
