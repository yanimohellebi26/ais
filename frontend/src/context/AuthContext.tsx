import React, {
    createContext,
    useContext,
    useEffect,
    useState,
    ReactNode,
    useRef,
} from "react";
import { jwtDecode } from "jwt-decode";
import { clearLastVisitedRoute } from "../hooks/useLastVisitedRoute";

type User = {
    token: string | null;
    role: string | null;
    id?: number | null ;
};

type AuthContextType = {
    user: User;
    login: (token: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User>({ token: null, role: null });
    const logoutTimerRef = useRef<number | null>(null);


    /** Decode jwt token and return user role */
    const extractRoleFromToken = (token: string): string | null => {
        try {
            const decoded: any = jwtDecode(token);
            const now = Date.now() / 1000;

            // Check jwt exp
            if (decoded.exp && decoded.exp < now) {
                console.warn("Token expired");
                localStorage.removeItem("token");
                return null;
            }

            return decoded.role || null;
        } catch (err) {
            console.error("Error while decode jwt", err);
            localStorage.removeItem("token");
            return null;
        }
    };

    /** Decode jwt token and return user id */
    const extractIdFromToken = (token: string): number | null => {
        try {
            const decoded: any = jwtDecode(token);
            const now = Date.now() / 1000;

            // check jwp exp
            if (decoded.exp && decoded.exp < now) {
                console.warn("Token expired");
                localStorage.removeItem("token");
                return null;
            }

            return decoded.id || decoded.sub || null;
        } catch (err) {
            console.error("Error while decoding jwt for id", err);
            localStorage.removeItem("token");
            return null;
        }
    };

    /** Auto logout when token expired */
    const scheduleLogout = (token: string) => {
        try {
            const decoded: any = jwtDecode(token);
            if (!decoded.exp) return;

            const expiresIn = decoded.exp * 1000 - Date.now();

            const MAX_TIMEOUT = 2147483647;

            if (expiresIn <= 0) {
                logout();
                return;
            }

            if (expiresIn > MAX_TIMEOUT) {
                return;
            }

            if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current);
            logoutTimerRef.current = setTimeout(() => {
                console.log("Token expired, auto logout");
                logout();
            }, expiresIn);
        } catch (err) {
            console.error("Can't plan logout :", err);
        }
    };

    /** Login */
    const login = (token: string) => {
        const role = extractRoleFromToken(token);
        if (!role) return;
        const id = extractIdFromToken(token);
        

        localStorage.setItem("token", token);
        setUser({ token, role, id });
        scheduleLogout(token);
    };

    /** Logout */
    const logout = () => {
        localStorage.removeItem("token");
        setUser({ token: null, role: null });

        // Clear last visited route
        clearLastVisitedRoute();

        if (logoutTimerRef.current) {
            clearTimeout(logoutTimerRef.current);
            logoutTimerRef.current = null;
        }
    };

    /** Check JWT at launch */
    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) {
            const role = extractRoleFromToken(token);
            if (role) {
                const id = extractIdFromToken(token);
                setUser({ token, role ,id });
                scheduleLogout(token);
            } else {
                logout();
            }
        }
        return () => {
            if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current);
        };
    }, []);

    const isAuthenticated = !!user.token;

    return (
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context)
        throw new Error("useAuth must be used within an AuthProvider");
    return context;
};
