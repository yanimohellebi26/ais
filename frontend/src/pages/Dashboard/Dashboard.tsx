import React from "react";
import { Routes, Route } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import DashboardHome from "./DashboardHome";
import DashboardShips from "../Ships/DashboardShips";
import Account from "../Account/Account"

const Dashboard: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<DashboardLayout />}>
                <Route index element={<DashboardHome />} />
                <Route path="ships/*" element={<DashboardShips />} />
                <Route path="account/*" element={<Account />}/>
            </Route>
        </Routes>
    );
};

export default Dashboard;
