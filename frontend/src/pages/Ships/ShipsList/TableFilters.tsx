import React, { useState, useEffect, useMemo } from "react";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { ChevronDown, ChevronRight } from "lucide-react";
import { VesselFilters , VesselType } from "./interfaces";
import { Country } from "./interfaces";
import {useLoading} from "../../../context/LoadingContext";

interface Props {
    filters: VesselFilters;
    onFiltersChange: (filters: VesselFilters) => void;
    onReset: () => void;
}

const TableFilters: React.FC<Props> = ({ filters, onFiltersChange, onReset }) => {
    const [localFilters, setLocalFilters] = useState<VesselFilters>(filters);
    const [isExpanded, setIsExpanded] = useState(false);
    const [countries, setCountries] = useState<Country[]>([]);
    const [vesselTypes, setVesselTypes] = useState<VesselType[]>([]);
    const api = useApi();
    const {loading, setLoading} = useLoading();

    // Fetch countries on mount
    useEffect(() => {
        async function fetchCountries() {
            try {
                setLoading(true);
                const response = await api("/api/v1/country", {
                    method: "GET",
                    headers: { "Content-Type": "application/json" }
                });
                setCountries(response || []);
            } catch (e) {
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
                    headers: { "Content-Type": "application/json" }
                });
                setVesselTypes(response || []);
            } catch (e) {
                toast.error("Failed to load vessel types");
            } finally {
                setLoading(false);
            }
        }
        fetchVesselTypes();
    }, []);

    // Group countries by name and collect all their MIDs
    const groupedCountries = useMemo(() => {
        const countryMap = new Map<string, { mids: number[], alpha2: string }>();

        countries.forEach(country => {
            if (!countryMap.has(country.name)) {
                countryMap.set(country.name, { mids: [], alpha2: country.alpha2 });
            }
            countryMap.get(country.name)!.mids.push(country.mid);
        });

        return Array.from(countryMap.entries()).map(([name, data]) => ({
            name,
            alpha2: data.alpha2,
            mids: data.mids.sort((a, b) => a - b)
        }));
    }, [countries]);

    // Extract unique vessel groups
    const vesselGroups = useMemo(() => {
        const groups = Array.from(new Set(vesselTypes.map(v => v.vesselGroup)));
        return groups.sort();
    }, [vesselTypes]);

    // Debounce filter changes
    useEffect(() => {
        const handler = setTimeout(() => {
            onFiltersChange(localFilters);
        }, 800);

        return () => clearTimeout(handler);
    }, [localFilters, onFiltersChange]);

    const handleChange = (key: keyof VesselFilters, value: any) => {
        setLocalFilters(prev => ({
            ...prev,
            [key]: value === "" ? undefined : value
        }));
    };

    const handleCountryChange = (value: string) => {
        setLocalFilters(prev => ({
            ...prev,
            country: value === "" ? undefined : value
        }));
    };

    const handleReset = () => {
        setLocalFilters({});
        onReset();
    };

    const activeFiltersCount = Object.values(localFilters).filter(v => v !== undefined && v !== "").length;

    return (
        <div className="card bg-base-200 mb-4">
            <div className="card-body p-4">
                <div className="flex justify-between items-center">
                    <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        {isExpanded ? <ChevronDown /> : <ChevronRight />} Advanced Filters
                        {activeFiltersCount > 0 && (
                            <span className="badge badge-primary badge-sm ml-2">
                                {activeFiltersCount}
                            </span>
                        )}
                    </button>
                    {activeFiltersCount > 0 && (
                        <button className="btn btn-sm btn-outline" onClick={handleReset}>
                            Reset All
                        </button>
                    )}
                </div>

                {isExpanded && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                        {/* Country - Dropdown */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Country</span>
                            </label>
                            <select
                                className="select select-bordered select-sm w-full"
                                value={localFilters.country || ""}
                                onChange={e => handleCountryChange(e.target.value)}
                                disabled={loading}
                            >
                                <option value="">All countries</option>
                                {groupedCountries.map(country => (
                                    <option key={country.name} value={country.name}>
                                        {country.name} {country.alpha2} ({country.mids.join(', ')})
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* VesselGroup - Dropdown */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Vessel group</span>
                            </label>
                            <select
                                className="select select-bordered select-sm w-full"
                                value={localFilters.vesselGroup || ""}
                                onChange={e => handleChange("vesselGroup", e.target.value)}
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

                        {/* Min Length */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Min Length (m)</span>
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                placeholder="Min length"
                                className="input input-bordered input-sm w-full"
                                value={localFilters.minLength || ""}
                                onChange={e => handleChange("minLength", e.target.value ? parseFloat(e.target.value) : undefined)}
                            />
                        </div>

                        {/* Max Length */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Max Length (m)</span>
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                placeholder="Max length"
                                className="input input-bordered input-sm w-full"
                                value={localFilters.maxLength || ""}
                                onChange={e => handleChange("maxLength", e.target.value ? parseFloat(e.target.value) : undefined)}
                            />
                        </div>

                        {/* Min Width */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Min Width (m)</span>
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                placeholder="Min Width"
                                className="input input-bordered input-sm w-full"
                                value={localFilters.minWidth || ""}
                                onChange={e => handleChange("minWidth", e.target.value ? parseFloat(e.target.value) : undefined)}
                            />
                        </div>

                        {/* Max Width */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Max Width (m)</span>
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                placeholder="Max Width"
                                className="input input-bordered input-sm w-full"
                                value={localFilters.maxWidth || ""}
                                onChange={e => handleChange("maxWidth", e.target.value ? parseFloat(e.target.value) : undefined)}
                            />
                        </div>

                        {/* Min Draft */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Min Draft (m)</span>
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                placeholder="Min draft"
                                className="input input-bordered input-sm w-full"
                                value={localFilters.minDraft || ""}
                                onChange={e => handleChange("minDraft", e.target.value ? parseFloat(e.target.value) : undefined)}
                            />
                        </div>

                        {/* Max Draft */}
                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Max Draft (m)</span>
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                placeholder="Max draft"
                                className="input input-bordered input-sm w-full"
                                value={localFilters.maxDraft || ""}
                                onChange={e => handleChange("maxDraft", e.target.value ? parseFloat(e.target.value) : undefined)}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TableFilters;