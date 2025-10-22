import React, {
    createContext,
    useContext,
    useState,
    useCallback,
    ReactNode,
} from "react";

interface LoadingContextType {
    loading: boolean;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    withLoading: (fn: () => Promise<void>) => Promise<void>;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export function useLoading(): LoadingContextType {
    const context = useContext(LoadingContext);
    if (!context) {
        throw new Error("useLoading must be used within a LoadingProvider");
    }
    return context;
}

export function LoadingProvider({ children }: { children: ReactNode }) {
    const [loading, setLoading] = useState(false);

    const withLoading = useCallback(async (fn: () => Promise<void>) => {
        setLoading(true);
        try {
            await fn();
        } finally {
            setLoading(false);
        }
    }, []);

    return (
        <LoadingContext.Provider value={{ loading, setLoading, withLoading }}>
            {children}
            {loading && <GlobalLoader />}
        </LoadingContext.Provider>
    );
}

function GlobalLoader() {
    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black/10 z-50">
            <span className="loading loading-bars loading-xl w-15 text-primary"></span>
        </div>
    );
}
