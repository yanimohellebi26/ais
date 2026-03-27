import React, {useState} from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import {AnalyticsFilters} from "./interfaces";
import TableFilters from "./TableFilters";
import BaseModule from "../../../components/BaseComponents/BaseModule";
import { useNavigate } from "react-router-dom";
import TrafficDensityWidget from "../../Map/components/TrafficDensityWidget";

const AnalyticsAllModules: React.FC = () => {

    const [filters, setFilters] = useState<AnalyticsFilters>({})
    const navigate = useNavigate();


    return (
        <>
            <Breadcrumbs/>
            <div className="flex justify-between mb-6">
                <h1 className="text-2xl font-semibold mr-4">Analytics</h1>
            </div>

            <TableFilters
                filters={filters}
                onFiltersChange={(newFilters) => setFilters(newFilters)}
                onReset={() => setFilters({})}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <BaseModule
                    title="Traffic Density"
                    onClick={() => navigate("traffic-density")}
                >
                    <TrafficDensityWidget />

                    <p className="text-sm text-gray-500">
                        Visualize vessel density with a heatmap
                    </p>
                </BaseModule>
            </div>

        </>
    );
};

export default AnalyticsAllModules;