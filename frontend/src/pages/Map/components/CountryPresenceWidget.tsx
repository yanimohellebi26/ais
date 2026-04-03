import React from "react";
import { useCountryPresence } from "../../../hooks/useCountryPresence";
import { AnalyticsFilters } from "../../Analytics/Components/interfaces";

interface Props {
    filters?: AnalyticsFilters;
}

const CountryPresenceWidget: React.FC<Props> = ({ filters }) => {
    const { data, loading } = useCountryPresence({ filters, topN: 5 });

    if (loading) {
        return (
            <div className="flex justify-center items-center h-[150px]">
                <span className="loading loading-spinner loading-sm" />
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="flex justify-center items-center h-[150px] text-sm text-base-content/50">
                No data available
            </div>
        );
    }

    const max = data[0].vesselCount;

    return (
        <div className="flex flex-col gap-1 w-full" style={{ height: 150, overflowY: "auto" }}>
            {data.map((item) => (
                <div key={item.alpha2} className="flex items-center gap-2 text-xs">
                    <span className="w-24 truncate text-base-content/70 shrink-0">{item.countryName}</span>
                    <div className="flex-1 bg-base-300 rounded-full h-2 overflow-hidden">
                        <div
                            className="bg-primary h-2 rounded-full"
                            style={{ width: `${(item.vesselCount / max) * 100}%` }}
                        />
                    </div>
                    <span className="w-6 text-right font-semibold text-base-content shrink-0">
                        {item.vesselCount}
                    </span>
                </div>
            ))}
        </div>
    );
};

export default CountryPresenceWidget;