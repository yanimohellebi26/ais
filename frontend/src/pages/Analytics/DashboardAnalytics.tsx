import React from "react";
import { Route, Routes } from "react-router-dom";
import AnalyticsAllModules from "./Components/AnalyticsAllModules";
import TrafficDensityModule from "./Components/TrafficDensityModule";
import CountryPresenceModule from "./Components/CountryPresenceModule";
import VesselTypeStatisticsModule from "./Components/VesselTypeStatisticsModule";

const DashboardAnalytics: React.FC = () => {
    return (
        <Routes>
            <Route index element={<AnalyticsAllModules />} />
            <Route path="traffic-density" element={<TrafficDensityModule />} />
            <Route path="country-presence" element={<CountryPresenceModule />} />
            <Route path="vessel-type-statistics" element={<VesselTypeStatisticsModule />} />
        </Routes>
    );
};
export default DashboardAnalytics;