import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const LAST_ROUTE_KEY = 'lastVisitedRoute';

/**
 * Hook to save and restore the last visited route
 */
export const useLastVisitedRoute = () => {
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        const excludedPaths = ['/login', '/register', '/'];

        if (!excludedPaths.includes(location.pathname)) {
            localStorage.setItem(LAST_ROUTE_KEY, location.pathname);
        }
    }, [location.pathname]);

    const restoreLastRoute = () => {
        const lastRoute = localStorage.getItem(LAST_ROUTE_KEY);

        if (lastRoute && lastRoute !== '/login' && lastRoute !== '/register') {
            navigate(lastRoute, { replace: true });
            return true;
        }
        return false;
    };

    const clearLastRoute = () => {
        localStorage.removeItem(LAST_ROUTE_KEY);
    };

    return {
        restoreLastRoute,
        clearLastRoute
    };
};

export const getLastVisitedRoute = (): string | null => {
    return localStorage.getItem(LAST_ROUTE_KEY);
};

export const clearLastVisitedRoute = () => {
    localStorage.removeItem(LAST_ROUTE_KEY);
};