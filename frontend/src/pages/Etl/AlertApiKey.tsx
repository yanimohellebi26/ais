import React, {useState} from "react";
import {useEtlAuth} from "../../context/EtlAuthContext";
import {useNavigate} from "react-router-dom";
import {ArrowRight, CircleX} from "lucide-react";

const AlertApiKey: React.FC = () => {
    const { apiKey } = useEtlAuth();
    const navigate = useNavigate();

    return (
        <div className="flex items-end">
            {apiKey === "" ? (
                <div
                    className="badge badge-error badge-soft cursor-pointer hover:border-error"
                    onClick={ ()=> navigate("/dashboard/etl/settings")} >
                    <CircleX className="w-4"/>
                    No key found
                    <ArrowRight />
                </div>
            ) : ""
            }
        </div>
    );
};

export default AlertApiKey;