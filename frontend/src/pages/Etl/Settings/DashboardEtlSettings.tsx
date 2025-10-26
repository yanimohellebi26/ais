import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import ApiKeyForm from "./ApiKeyForm";

const DashboardEtlSettings: React.FC = () => {
    return (
        <>
            <div className="flex item-center justify-between mb-4">
                <Breadcrumbs/>
            </div>
            <h1 className="text-2xl font-semibold">Settings</h1>
            <p className="text-base-content/70 mb-4">Manage AIS Data platform configuration</p>
            <ApiKeyForm/>
        </>
    );
};

export default DashboardEtlSettings;
