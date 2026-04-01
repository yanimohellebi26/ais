import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import TrafficDensityMap from "../../Map/components/TrafficDensityMap";
import {ArrowLeft} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

interface Props {
    filters?: any;
}

const TrafficDensityModule: React.FC<Props> = ({ filters }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters = filters || (location.state as any)?.filters || {};

    return (
        <>
            <Breadcrumbs />
            <div className="flex gap-4 mt-4">
                <button className="btn btn-sm btn-outline" onClick={() => navigate("/dashboard/analytics", { state: { filters: initialFilters } })}>
                    <ArrowLeft />
                    Back
                </button>
                <h1 className="text-2xl font-semibold pb-4">Traffic Density Heatmap</h1>
            </div>

            <TrafficDensityMap filters={initialFilters} />
        </>
    );
};

export default TrafficDensityModule;