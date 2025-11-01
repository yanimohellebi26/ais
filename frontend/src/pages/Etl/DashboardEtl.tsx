import React from "react";
import {Route, Routes} from "react-router-dom";
import DashboardEtlSettings from "./Settings/DashboardEtlSettings";
import DashboardEtlRunner from "./Runner/DashboardEtlRunner";
import DashboardEtlPipelines from "./Pipelines/DashboardEtlPipelines";
import DashboardEtlHistory from "./History/DashboardEtlHistory";

const DashboardEtl: React.FC = () => {
    return (
        <Routes>
            <Route index element={<DashboardEtlRunner/>} />
            <Route path="runner" element={<DashboardEtlRunner/>} />
            <Route path="settings" element={<DashboardEtlSettings/>} />
            <Route path="pipelines" element={<DashboardEtlPipelines/>} />
            <Route path="history" element={<DashboardEtlHistory/>} />
        </Routes>
    );
};

export default DashboardEtl;
