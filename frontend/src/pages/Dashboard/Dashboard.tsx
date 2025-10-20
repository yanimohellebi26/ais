import React from "react";
import { Routes, Route } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import DashboardHome from "./DashboardHome";
import DashboardShips from "../Ships/DashboardShips";
import DashboardAdminPage from "../Admin/DashboardAdminPage";

const Dashboard: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<DashboardLayout />}>
                <Route index element={<DashboardHome />} />
                <Route path="ships/*" element={<DashboardShips />} />
                <Route path="admin/*" element={<DashboardAdminPage />}/>
            </Route>
        </Routes>
    );
};

export default Dashboard;
