import React from "react";
import {Route, Routes} from "react-router-dom";
import DashboardShipsList from "./ShipsList/DashboardShipsList";
import DashboardShipsMyShips from "./MyShips/DashboardShipsMyShips";
import ShipDetail from "./MyShips/ShipDetail";

const DashboardShips: React.FC = () => {
    return (
        <Routes>
            <Route index element={<DashboardShipsList />} />
            <Route path="list" element={<DashboardShipsList />} />
            <Route path="my-ships" element={<DashboardShipsMyShips />} />
            <Route path="my-ships/:id" element={<ShipDetail />} />
        </Routes>
    );
};

export default DashboardShips;
