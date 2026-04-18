import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import PortRoutesMap from "../../Map/components/PortRoutesMap";
import { ArrowLeft } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

interface Props {
    filters?: any;
}

const PortRoutesModule: React.FC<Props> = ({ filters }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters = filters || (location.state as any)?.filters || {};

    return (
        <>
            <Breadcrumbs />
            
            <div className="flex gap-4 mt-4">
                <button 
                    className="btn btn-sm btn-outline" 
                    onClick={() => navigate("/dashboard/analytics", { state: { filters: initialFilters } })}
                >
                    <ArrowLeft size={18} />
                    Back
                </button>
                <h1 className="text-2xl font-semibold pb-4">Maritime Port Corridors</h1>
            </div>

            <div className="w-full h-[calc(100vh-200px)] rounded-lg overflow-hidden shadow-lg border border-base-300">
                <PortRoutesMap filters={initialFilters} />
            </div>
        </>
    );
};

export default PortRoutesModule;