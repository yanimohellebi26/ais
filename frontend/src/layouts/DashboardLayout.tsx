import React, { useState } from "react";
import Sidebar from "../components/Layouts/Sidebar";
import { Menu } from "lucide-react";
import { Outlet } from "react-router-dom";
import { useLastVisitedRoute } from "../hooks/useLastVisitedRoute";

const DashboardLayout: React.FC = () => {
    const [sidebarFolded, setSidebarFolded] = useState(false);

    // Start tracking last visited route
    useLastVisitedRoute();

    return (
        <div className="drawer lg:drawer-open">
            <input id="dashboard-drawer" type="checkbox" className="drawer-toggle" />

            <div className="drawer-content flex flex-col bg-base-300">
                {/* Navbar mobile*/}
                <div className="w-full navbar bg-base-100 shadow-sm lg:hidden">
                    <div className="flex-none">
                        <label
                            htmlFor="dashboard-drawer"
                            className="btn btn-square btn-ghost"
                        >
                            <Menu className="h-5 w-5" />
                        </label>
                    </div>
                    <div className="flex-1 px-2 font-semibold text-lg">Sea Sight </div>
                </div>

                {/* Main content */}
                <main className="flex-1 p-6 overflow-auto transition-all duration-300">
                    <Outlet /> {/* Child routes*/}
                </main>
            </div>

            {/* Sidebar */}
            <div className="drawer-side">
                <label
                    htmlFor="dashboard-drawer"
                    aria-label="close sidebar"
                    className="drawer-overlay"
                ></label>

                <Sidebar
                    folded={sidebarFolded}
                    onToggleFold={() => setSidebarFolded(!sidebarFolded)}
                />
            </div>
        </div>
    );
};

export default DashboardLayout;
