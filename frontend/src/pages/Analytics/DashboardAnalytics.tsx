import React from "react";
import { Route, Routes } from "react-router-dom";
import AnalyticsAllModules from "./Components/AnalyticsAllModules";
import TrafficDensityModule from "./Components/TrafficDensityModule";

const DashboardAnalytics: React.FC = () => {
    return (
        <Routes>
            <Route index element={<AnalyticsAllModules />} />
            <Route path="traffic-density" element={<TrafficDensityModule />} />
        </Routes>
    );
};
export default DashboardAnalytics;