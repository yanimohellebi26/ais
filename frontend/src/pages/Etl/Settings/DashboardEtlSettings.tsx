import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import ApiKeyForm from "./ApiKeyForm";
import AlertApiKey from "../AlertApiKey";

const DashboardEtlSettings: React.FC = () => {
    return (
        <>
            <div className="flex item-center justify-between mb-4">
                <Breadcrumbs/>
            </div>
            <h1 className="text-2xl font-semibold mr-4">ETL Settings</h1>

            <div className="flex items-center mb-4 gap-2">
                <p className="text-base-content/70 mb-4">Manage AIS Data platform configuration</p>
                <AlertApiKey />
            </div>

            <ApiKeyForm/>
        </>
    );
};

export default DashboardEtlSettings;
