import React from "react";
import TableShips from "./TableShips";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import Button from "../../../components/BaseComponents/Button";

const DashboardShipsList: React.FC = () => {
    return (
        <>
            <div className="flex item-center justify-between mb-4">
                <Breadcrumbs/>
                <Button className="btn btn-primary btn-sm">+ Add new ship</Button>
            </div>
            <TableShips />
        </>
    );
};

export default DashboardShipsList;
