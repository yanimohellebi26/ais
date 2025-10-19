import {LayoutDashboard, Ship, List, ShipWheel,UserRound,Users,ShieldUser} from "lucide-react";
import React from "react";

export type Role = "ROLE_ADMIN" | "ROLE_CAPTAIN" | "ROLE_FINANCIAL_ANALYST" | "ROLE_MARITIME_EXPERT" | "ROLE_OWNER";

export type MenuItem = {
    label: string;
    path?: string;
    roles?: Role[];
    icon?: React.ElementType;
    children?: MenuItem[];
};


export const menuItems: MenuItem[] = [
    { label: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
    { label: "Admin",
        icon: ShieldUser,
        path: "/dashboard/admin",
        roles: ["ROLE_ADMIN"],
        children: [
            {label: "List Users", path: "/dashboard/admin/list-users", icon: Users}
        ]
    },
    { label: "Ships",
        icon: Ship,
        path: "/dashboard/ships",
        roles: ["ROLE_CAPTAIN", "ROLE_OWNER", "ROLE_ADMIN"],
        children: [
            {label: "List ships", path:"/dashboard/ships/list", icon: List},
            {label: "My ships", path:"/dashboard/ships/my-ships", icon: ShipWheel},
        ]
    }
];
