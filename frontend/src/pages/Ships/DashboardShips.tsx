import React from "react";
import {Route, Routes} from "react-router-dom";
import DashboardShipsList from "./ShipsList/DashboardShipsList";
import DashboardShipsMyShips from "./MyShips/DashboardShipsMyShips";

const DashboardShips: React.FC = () => {
    return (
        <Routes>
            <Route index element={<DashboardShipsList />} />
            <Route path="list" element={<DashboardShipsList />} />
            <Route path="my-ships" element={<DashboardShipsMyShips />} />
        </Routes>
    );
};

export default DashboardShips;
