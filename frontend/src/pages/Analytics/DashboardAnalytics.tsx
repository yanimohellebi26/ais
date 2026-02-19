import React from "react";
import { Route, Routes } from "react-router-dom";
import AnalyticsAllModules from "./Components/AnalyticsAllModules";

const DashboardAnalytics: React.FC = () => {
    return (
        <Routes>
            <Route index element={<AnalyticsAllModules />} />
        </Routes>
    );
};
export default DashboardAnalytics;