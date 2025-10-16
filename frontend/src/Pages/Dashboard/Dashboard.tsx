import React from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import {Route, Routes} from "react-router-dom";
import DashboardHome from "./DashboardHome";
import DashboardShips from "../Ships/DashboardShips";

const Dashboard: React.FC = () => {
    return (
        <DashboardLayout>
            <Routes>
                <Route path="/" element={<DashboardHome />} />
                <Route path="ships" element={<DashboardShips />} />
                {/*<Route path="map" element={<Maps />} />*/}
            </Routes>
        </DashboardLayout>
    );
};

export default Dashboard;
