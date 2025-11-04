import React from "react";
import {Route, Routes} from "react-router-dom";
import MapComponent from "./MapComponent";

const DashboardMap: React.FC = () => {
    return (
        <Routes>
            <Route index element={<MapComponent />} />
        </Routes>
    );
};

export default DashboardMap;
