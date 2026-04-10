import React, {useState} from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import {AnalyticsFilters} from "./interfaces";
import TableFilters from "./TableFilters";
import BaseModule from "../../../components/BaseComponents/BaseModule";
import { useNavigate, useLocation } from "react-router-dom";
import TrafficDensityWidget from "../../Map/components/TrafficDensityWidget";
import CountryPresenceWidget from "../../Map/components/CountryPresenceWidget";

const AnalyticsAllModules: React.FC = () => {

    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters = (location.state as any)?.filters || {};
    const [filters, setFilters] = useState<AnalyticsFilters>(initialFilters)

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
                    onClick={() => navigate("traffic-density", { state: { filters } })}
                >
                    <TrafficDensityWidget filters={filters} />

                    <p className="text-sm text-gray-500">
                        Visualize vessel density with a heatmap
                    </p>
                </BaseModule>
                <BaseModule
                    title="Country Presence"
                    onClick={() => navigate("country-presence", { state: { filters } })}
                >
                    <CountryPresenceWidget filters={filters} />
                    <p className="text-sm text-gray-500">
                        Top countries by number of vessels detected
                    </p>
                </BaseModule>
                <BaseModule
                    title={"Vessel Type Statistics"}
                    onClick={() => navigate("vessel-type-statistics", { state: { filters } })}
                >
                    <p className="text-sm text-gray-500">
                        Compare vessel types across key metrics
                    </p>
                </BaseModule>
            </div>

        </>
    );
};

export default AnalyticsAllModules;