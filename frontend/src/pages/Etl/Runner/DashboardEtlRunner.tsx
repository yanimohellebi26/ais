import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import {ArrowRight, CircleX} from "lucide-react";
import {useEtlAuth} from "../../../context/EtlAuthContext";
import {useNavigate} from "react-router-dom";
import Commands from "./Commands";
import CarouselInfos from "./CarouselInfos";


const DashboardEtlRunner: React.FC = () => {
    const { apiKey } = useEtlAuth();
    const navigate = useNavigate();

    return (
        <>
            <div className="mb-4">
                <Breadcrumbs/>
            </div>
            <div className="flex items-end">
                <h1 className="text-2xl font-semibold mr-4">ETL Pipelines and Commands</h1>
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
            <p className="text-base-content/70 mb-4">Run pipelines, workflow & commands scripts</p>
            <div className="flex flex-col space-y-8">
                <CarouselInfos/>
                <Commands/>
            </div>
        </>
    );
};

export default DashboardEtlRunner;
