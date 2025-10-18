import {Role} from "../configs/sidebarConfig";
import React, {JSX} from "react";
import {useAuth} from "../context/AuthContext";
import {Navigate} from "react-router-dom";

type ProtectedRouteProps = {
    allowedRoles?: Role[];
    children: JSX.Element;
};

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
    const { user } = useAuth();

    if (!user.token) return <Navigate to="/login" replace />;

    if (allowedRoles && (!user.role || !allowedRoles.includes(user.role as Role))) {
        return <Navigate to="/" replace />;
    }

    return children;
};