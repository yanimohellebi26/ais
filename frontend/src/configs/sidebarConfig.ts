import {LayoutDashboard, Ship, Map} from "lucide-react";
import React from "react";

export type Role = "ROLE_ADMIN" | "ROLE_CAPTAIN" | "ROLE_FINANCIAL_ANALYST" | "ROLE_MARITIME_EXPERT" | "ROLE_OWNER";

export type MenuItem = {
    label: string;
    path: string;
    roles?: Role[];
    icon: React.ElementType;
};

export const menuItems: MenuItem[] = [
    { label: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
    { label: "Ships", icon: Ship, path: "/dashboard/ships", roles: ["ROLE_CAPTAIN", "ROLE_OWNER", "ROLE_ADMIN"] },
    { label: "Maps", icon: Map, path: "/dashboard/map" },
];
