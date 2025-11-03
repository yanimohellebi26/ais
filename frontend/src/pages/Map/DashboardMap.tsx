import React from "react";
import {Route, Routes} from "react-router-dom";
import Map from "./Map";

const DashboardMap: React.FC = () => {
    return (
        <Routes>
            <Route index element={<Map />} />
        </Routes>
    );
};

export default DashboardMap;
