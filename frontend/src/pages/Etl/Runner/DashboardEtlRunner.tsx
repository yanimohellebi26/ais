import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import Commands from "./Commands";
import CarouselInfos from "./CarouselInfos";
import AlertApiKey from "../AlertApiKey";


const DashboardEtlRunner: React.FC = () => {
    return (
        <>
            <div className="mb-4">
                <Breadcrumbs/>
            </div>
            <h1 className="text-2xl font-semibold mr-4">ETL Commands</h1>

            <div className="flex items-center mb-4 gap-2">
                <p className="text-base-content/70">Run commands scripts</p>
                <AlertApiKey />
            </div>
            <div className="flex flex-col space-y-8">
                <CarouselInfos/>
                <Commands/>
            </div>
        </>
    );
};

export default DashboardEtlRunner;
