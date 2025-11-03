import React, {useEffect, useState} from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import ApiKeyForm from "./ApiKeyForm";
import AlertApiKey from "../AlertApiKey";
import {useEtlApi} from "../../../hooks/useEtlApi";
import CreateApiKeys from "./CreateApiKeys";

const DashboardEtlSettings: React.FC = () => {
    const api = useEtlApi();
    const [isSuperUser, setIsSuperUser] = useState(false);
    useEffect(() => {
        const fetchSuperUser = async () => {
            try {
                const response = await api("/apiKeys/isSuperUser/", {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                });
                setIsSuperUser(response)
            } catch {}
        };
        fetchSuperUser();
    }, []);

    return (
        <>
            <div className="flex item-center justify-between mb-4">
                <Breadcrumbs/>
            </div>
            <h1 className="text-2xl font-semibold mr-4">ETL Settings</h1>

            <div className="flex items-center mb-4 gap-2">
                <p className="text-base-content/70">Manage AIS Data platform configuration</p>
                <AlertApiKey />
            </div>

            <ApiKeyForm/>
            {isSuperUser && (
                <CreateApiKeys/>
            )}
        </>
    );
};

export default DashboardEtlSettings;
