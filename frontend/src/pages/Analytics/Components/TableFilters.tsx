import React, { useEffect, useMemo, useState } from "react";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useLoading } from "../../../context/LoadingContext";
import {AnalyticsFilters} from "./interfaces"


interface Props {
    filters: AnalyticsFilters;
    onFiltersChange: (filters: AnalyticsFilters) => void;
    onReset: () => void;
}

const TableFilters: React.FC<Props> = ({
                                               filters,
                                               onFiltersChange,
                                               onReset
                                           }) => {

    const [localFilters, setLocalFilters] =
        useState<AnalyticsFilters>(filters);

    const [isExpanded, setIsExpanded] = useState(true);
    const [countries, setCountries] = useState<any[]>([]);
    const [vesselTypes, setVesselTypes] = useState<any[]>([]);

    const api = useApi();
    const { loading, setLoading } = useLoading();

    useEffect(() => {
        async function fetchCountries() {
            try {
                setLoading(true);
                const response = await api("/api/v1/country", {
                    method: "GET",
                });
                setCountries(response || []);
            } catch {
                toast.error("Failed to load countries");
            } finally {
                setLoading(false);
            }
        }
        fetchCountries();
    }, []);

    useEffect(() => {
        async function fetchVesselTypes() {
            try {
                setLoading(true);
                const response = await api("/api/v1/vessel-type", {
                    method: "GET",
                });
                setVesselTypes(response || []);
            } catch {
                toast.error("Failed to load vessel types");
            } finally {
                setLoading(false);
            }
        }
        fetchVesselTypes();
    }, []);

    const groupedCountries = useMemo(() => {
        const map = new Map<string, { mids: number[] }>();

        countries.forEach((c) => {
            if (!map.has(c.name)) {
                map.set(c.name, { mids: [] });
            }
            map.get(c.name)!.mids.push(c.mid);
        });

        return Array.from(map.entries()).map(([name, data]) => ({
            name,
            mids: data.mids
        }));
    }, [countries]);

    const vesselGroups = useMemo(() => {
        const groups = Array.from(
            new Set(vesselTypes.map(v => v.vesselGroup))
        );
        return groups.sort();
    }, [vesselTypes]);

    useEffect(() => {
        if (
            localFilters.dateFrom &&
            localFilters.dateTo &&
            localFilters.dateFrom > localFilters.dateTo
        ) {
            setLocalFilters(prev => ({
                ...prev,
                dateTo: prev.dateFrom
            }));
        }
    }, [localFilters.dateFrom]);

    useEffect(() => {
        const handler = setTimeout(() => {
            onFiltersChange(localFilters);
        }, 800);

        return () => clearTimeout(handler);
    }, [localFilters]);

    const handleChange = (key: keyof AnalyticsFilters, value: any) => {
        setLocalFilters(prev => ({
            ...prev,
            [key]: value === "" ? undefined : value
        }));
    };

    const handleReset = () => {
        setLocalFilters({});
        onReset();
    };

    const activeFiltersCount =
        Object.values(localFilters).filter(v => v !== undefined && v !== "").length;

    return (
        <div className="card bg-base-200 mb-4">
            <div className="card-body p-4">

                <div className="flex justify-between items-center">
                    <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        {isExpanded ? <ChevronDown /> : <ChevronRight />}
                        Analytics Filters
                        {activeFiltersCount > 0 && (
                            <span className="badge badge-primary badge-sm ml-2">
                                {activeFiltersCount}
                            </span>
                        )}
                    </button>

                    {activeFiltersCount > 0 && (
                        <button
                            className="btn btn-sm btn-outline"
                            onClick={handleReset}
                        >
                            Reset All
                        </button>
                    )}
                </div>

                {isExpanded && (
                    <div className="space-y-4 mt-4">

                        {/* DATES */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Date From</span>
                                </label>
                                <input
                                    type="date"
                                    className="input input-bordered input-sm w-full"
                                    value={localFilters.dateFrom || ""}
                                    max={localFilters.dateTo || undefined}
                                    onChange={e =>
                                        handleChange("dateFrom", e.target.value)
                                    }
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Date To</span>
                                </label>
                                <input
                                    type="date"
                                    className="input input-bordered input-sm w-full"
                                    value={localFilters.dateTo || ""}
                                    min={localFilters.dateFrom || undefined}
                                    onChange={e =>
                                        handleChange("dateTo", e.target.value)
                                    }
                                />
                            </div>
                        </div>

                        {/* COUNTRY + VESSEL TYPE */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Country</span>
                                </label>
                                <select
                                    className="select select-bordered select-sm w-full"
                                    value={localFilters.country || ""}
                                    onChange={e =>
                                        handleChange("country", e.target.value)
                                    }
                                    disabled={loading}
                                >
                                    <option value="">All countries</option>
                                    {groupedCountries.map(c => (
                                        <option key={c.name} value={c.name}>
                                            {c.name} ({c.mids.join(", ")})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Vessel Group</span>
                                </label>
                                <select
                                    className="select select-bordered select-sm w-full"
                                    value={localFilters.vesselGroup || ""}
                                    onChange={e =>
                                        handleChange("vesselGroup", e.target.value)
                                    }
                                    disabled={loading}
                                >
                                    <option value="">All vessel groups</option>
                                    {vesselGroups.map(group => (
                                        <option key={group} value={group}>
                                            {group}
                                        </option>
                                    ))}
                                </select>
                            </div>

                        </div>

                        {/* LATITUDE / LONGITUDE / RADIUS SUR UNE LIGNE */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Latitude</span>
                                </label>
                                <input
                                    type="number"
                                    className="input input-bordered input-sm w-full"
                                    value={localFilters.latitude || ""}
                                    onChange={e =>
                                        handleChange(
                                            "latitude",
                                            e.target.value
                                                ? parseFloat(e.target.value)
                                                : undefined
                                        )
                                    }
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Longitude</span>
                                </label>
                                <input
                                    type="number"
                                    className="input input-bordered input-sm w-full"
                                    value={localFilters.longitude || ""}
                                    onChange={e =>
                                        handleChange(
                                            "longitude",
                                            e.target.value
                                                ? parseFloat(e.target.value)
                                                : undefined
                                        )
                                    }
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Radius (meters)</span>
                                </label>
                                <input
                                    type="number"
                                    className="input input-bordered input-sm w-full"
                                    value={localFilters.radius || ""}
                                    onChange={e =>
                                        handleChange(
                                            "radius",
                                            e.target.value
                                                ? parseFloat(e.target.value)
                                                : undefined
                                        )
                                    }
                                />
                            </div>
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
};

export default TableFilters;