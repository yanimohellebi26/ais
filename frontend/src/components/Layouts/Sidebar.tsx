import React, { useState } from "react";
import {Link, useLocation, useNavigate} from "react-router-dom";
import { menuItems, Role, MenuItem } from "../../configs/sidebarConfig";
import { useAuth } from "../../context/AuthContext";
import {
    Ship,
    ChevronLeft,
    ChevronRight,
} from "lucide-react";
import Logout from "../BaseComponents/Logout";

interface SidebarProps {
    folded: boolean;
    onToggleFold: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ folded, onToggleFold }) => {
    const { user } = useAuth();
    const role = user?.role as Role | null;

    const filteredMenu: MenuItem[] = menuItems.filter(item => {
        if (!item.roles || item.roles.length === 0) return true;
        return role ? item.roles.includes(role) : false;
    });

    const location = useLocation();
    const currentPath = location.pathname;

    const [openMenus, setOpenMenus] = useState<Record<string, boolean>>({});

    const toggleSubMenu = (label: string) => {
        setOpenMenus(prev => ({ ...prev, [label]: !prev[label] }));
    };

    return (
        <aside
            className={`h-full bg-base-100 text-base-content shadow-sm transition-all duration-400 flex flex-col ${
                folded ? "w-20" : "w-64"
            }`}
        >
            {/* Header */}
            <div
                className={`flex items-center justify-between border-b border-base-300 p-4 ${
                    folded ? "justify-center" : ""
                }`}
            >
                {!folded && (
                    <>
                        <Link to="/" className="flex items-center space-x-2">
                            <Ship className="h-8 w-8 text-primary" />
                            <span className="text-xl font-semibold">Sea Sight</span>
                        </Link>
                    </>
                )}
                {folded && <Ship className="h-8 w-8 text-primary" />}

                {/* Toggle button (desktop) */}
                <button
                    onClick={onToggleFold}
                    className="btn btn-ghost btn-sm hidden lg:flex"
                >
                    {folded ? <ChevronRight /> : <ChevronLeft />}
                </button>
            </div>

            {/* Menu */}
            <nav className="flex-1 overflow-y-auto p-2">
                <ul className="flex flex-col gap-2">
                    {filteredMenu.map(item => {
                        const isActive =
                            currentPath === item.path ||
                            (item.children?.some(sub => sub.path === currentPath));

                        const hasChildren = item.children && item.children.length > 0;
                        const isOpen = openMenus[item.label];
                        const navigate = useNavigate();

                        const handleClick = () => {
                            if (hasChildren) {
                                if (folded) {
                                    // Sidebar fold -> 1st children
                                    const firstChildPath = item.children![0].path;
                                    if (firstChildPath) navigate(firstChildPath);
                                } else {
                                    // 🔹 Sidebar unfold -> toggle sub-menu
                                    toggleSubMenu(item.label);
                                }
                            }
                        };

                        return (
                            <li key={item.label} className="relative group">
                                {hasChildren ? (
                                    <div
                                        onClick={handleClick}
                                        className={`flex items-center gap-x-4 rounded-xl px-4 py-2 cursor-pointer transition-all duration-500 ${
                                            isActive
                                                ? "bg-primary/10 text-primary font-semibold"
                                                : "hover:bg-base-300 hover:text-base-content"
                                        } ${folded ? "justify-center" : ""}`}
                                    >
                                        {item.icon && (
                                            <item.icon className="h-5 w-5 transition-transform group-hover:scale-110" />
                                        )}
                                        {!folded && (
                                            <>
                                                <span>{item.label}</span>
                                                <ChevronRight
                                                    className={`ml-auto transition-transform duration-200 ${
                                                        isOpen ? "rotate-90" : ""
                                                    }`}
                                                />
                                            </>
                                        )}
                                    </div>
                                ) : (
                                    <Link
                                        to={item.path!}
                                        className={`flex items-center gap-x-4 rounded-xl px-4 py-2 ${
                                            isActive
                                                ? "bg-primary/10 text-primary font-semibold"
                                                : "hover:bg-base-300 hover:text-base-content"
                                        } ${folded ? "justify-center" : ""}`}
                                    >
                                        {item.icon && (
                                            <item.icon className="h-5 w-5 transition-transform group-hover:scale-110" />
                                        )}
                                        {!folded && <span>{item.label}</span>}
                                    </Link>
                                )}

                                {/* Sub menu */}
                                {hasChildren && isOpen && !folded && (
                                    <ul className="ml-8 mt-1 flex flex-col gap-1 border-l border-base-300 pl-3">
                                        {item.children!.map(sub => {
                                            const isSubActive = currentPath === sub.path;
                                            return (
                                                <li key={sub.path}>
                                                    <Link
                                                        to={sub.path!}
                                                        className={`flex items-center gap-x-3 rounded-lg px-3 py-2 ${
                                                            isSubActive
                                                                ? "bg-primary/10 text-primary font-semibold"
                                                                : "hover:bg-base-300 hover:text-base-content"
                                                        }`}
                                                    >
                                                        {sub.icon && <sub.icon className="h-4 w-4" />}
                                                        <span>{sub.label}</span>
                                                    </Link>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                )}
                            </li>
                        );
                    })}
                </ul>
            </nav>

            <div className="flex justify-center text-center p-2">
                <Logout />
            </div>
        </aside>
    );
};

export default Sidebar;
