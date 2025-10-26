import React from "react";
import {Route, Routes} from "react-router-dom";
import DashboardEtlSettings from "./Settings/DashboardEtlSettings";

const DashboardEtl: React.FC = () => {
    return (
        <Routes>
            <Route index element={<DashboardEtlSettings/>} />
            <Route path="settings" element={<DashboardEtlSettings/>} />
        </Routes>
    );
};

export default DashboardEtl;
