import {
    LayoutDashboard,
    Ship,
    List,
    ShipWheel,
    Users,
    ShieldUser,
    Workflow,
    Wrench,
    Map,
    Terminal,
    Orbit,
    History,
    FileText,
    TrendingUp
} from "lucide-react";
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
    { label: "Map", icon: Map, path: "/dashboard/map"},
    { label: "Admin",
        icon: ShieldUser,
        path: "/dashboard/admin",
        roles: ["ROLE_ADMIN"],
        children: [
            {label: "List Users", path: "/dashboard/admin/list-users", icon: Users},
            {label: "Request Property", path: "/dashboard/admin/request-property", icon: FileText}
        ]
    },
    { label: "Ships",
        icon: Ship,
        path: "/dashboard/ships",
        children: [
            {label: "List ships", path:"/dashboard/ships/list", icon: List},
            {label: "My ships", path:"/dashboard/ships/my-ships", roles: ["ROLE_CAPTAIN", "ROLE_OWNER", "ROLE_ADMIN"], icon: ShipWheel},
        ]
    },
    { label: "Analytics",
        icon: TrendingUp,
        path: "/dashboard/analytics",
        roles: ["ROLE_ADMIN", "ROLE_FINANCIAL_ANALYST", "ROLE_MARITIME_EXPERT"]
    },
    { label:"ETL",
        icon: Workflow,
        path: "/dashboard/etl",
        roles: ["ROLE_ADMIN"],
        children: [
            {label: "Runner", path: "/dashboard/etl/runner", icon: Terminal},
            {label: "Pipelines", path: "/dashboard/etl/pipelines", icon: Orbit},
            {label: "History", path: "/dashboard/etl/history", icon: History},
            {label: "Settings", path: "/dashboard/etl/settings", icon: Wrench},
        ]
    }
];
