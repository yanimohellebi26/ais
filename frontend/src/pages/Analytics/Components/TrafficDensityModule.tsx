import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import TrafficDensityMap from "../../Map/components/TrafficDensityMap";
import {ArrowLeft} from "lucide-react";
import { useNavigate} from "react-router-dom";

const TrafficDensityModule: React.FC = () => {
    const navigate = useNavigate();

    return (
        <>
            <Breadcrumbs />
            <div className="flex gap-4 mt-4">
                <button className="btn btn-sm btn-outline" onClick={() => navigate(-1)}>
                    <ArrowLeft />
                    Back
                </button>
                <h1 className="text-2xl font-semibold pb-4">Traffic Density Heatmap</h1>
            </div>

            <TrafficDensityMap />
        </>
    );
};

export default TrafficDensityModule;