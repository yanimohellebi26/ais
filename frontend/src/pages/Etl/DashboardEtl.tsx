import React from "react";
import {Route, Routes} from "react-router-dom";
import DashboardEtlSettings from "./Settings/DashboardEtlSettings";
import DashboardEtlRunner from "./Runner/DashboardEtlRunner";

const DashboardEtl: React.FC = () => {
    return (
        <Routes>
            <Route index element={<DashboardEtlRunner/>} />
            <Route path="runner" element={<DashboardEtlRunner/>} />
            <Route path="settings" element={<DashboardEtlSettings/>} />
        </Routes>
    );
};

export default DashboardEtl;
