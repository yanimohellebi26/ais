import React from "react";
import { LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const Logout: React.FC = () => {
    const { logout } = useAuth();

    return (
        <button className="btn btn-soft btn-error btn-sm w-full justify-start" onClick={logout}>
            <LogOut /> Logout
        </button>
    );
};

export default Logout;
