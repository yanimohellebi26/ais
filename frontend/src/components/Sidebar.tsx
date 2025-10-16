import React from "react";
import { Link, useLocation} from "react-router-dom";
import { menuItems, Role, MenuItem } from "../configs/sidebarConfig"
import { useAuth } from "../context/AuthContext";
import { Ship } from "lucide-react";

const Sidebar: React.FC = () => {
    const { user } = useAuth();
    const role = user.role as Role | null;

    const filteredMenu: MenuItem[] = menuItems.filter(item => {
        if (!item.roles || item.roles.length === 0) return true;
        return role ? item.roles.includes(role) : false;
    });

    const location = useLocation();
    const currentPath = location.pathname;


    return (
        <aside className="w-64 bg-base-100 text-base-content h-full shadow-sm">
            <ul className="flex flex-col gap-2 ">
                <li key="/" className="border-b border-base-300 p-6">
                    <Link to="/" className="flex items-center space-x-2 ">
                        <Ship className="h-8 w-8 text-primary" />
                        <span className="text-xl font-semibold">Sea Sight</span>
                    </Link>
                </li>
                <li key="" className="border-b border-base-300 p-6">
                    <Link to="" className="flex items-center space-x-2 ">

                    </Link>
                </li>
                <nav className="pt-4">
                    {filteredMenu.map(item => {
                        const isActive = currentPath === item.path;

                        return (
                            <li key={item.path} className="px-4 py-2">
                                <Link
                                    to={item.path}
                                    className={`
                                      px-4 py-2 rounded-xl flex items-center gap-x-4
                                      ${isActive ? "bg-primary/10 text-primary/90 font-semibold hover:bg-base-300" : "hover:bg-base-300 hover:text-base-content"}
                                    `}
                                >
                                    <item.icon className="h-4 w-4" />
                                    <span>{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}

                </nav>
            </ul>
        </aside>
    );
};

export default Sidebar;
