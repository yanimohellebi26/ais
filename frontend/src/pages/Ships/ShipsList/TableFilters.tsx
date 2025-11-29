import React, { useState, useEffect } from "react";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { ChevronDown, ChevronRight } from "lucide-react";
import { VesselFilters } from "./interfaces";
import { Country } from "./interfaces";



interface Props {
    filters: VesselFilters;
    onFiltersChange: (filters: VesselFilters) => void;
    onReset: () => void;
}

const TableFilters: React.FC<Props> = ({ filters, onFiltersChange, onReset }) => {
    const [localFilters, setLocalFilters] = useState<VesselFilters>(filters);
    const [isExpanded, setIsExpanded] = useState(false);
    const [countries, setCountries] = useState<Country[]>([]);
    const [loadingCountries, setLoadingCountries] = useState(false);

    const api = useApi();

    // Fetch countries on mount
    useEffect(() => {
        async function fetchCountries() {
            try {
                setLoadingCountries(true);
                const response = await api("/api/v1/country", {
                    method: "GET",
                    headers: { "Content-Type": "application/json" }
                });
                setCountries(response || []);
            } catch (e) {
                console.error("Failed to fetch countries:", e);
                toast.error("Failed to load countries");
            } finally {
                setLoadingCountries(false);
            }
        }
        fetchCountries();
    }, []);

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
        if (value === "") {
            setLocalFilters(prev => ({
                ...prev,
                country: undefined,
                mid: undefined
            }));
        } else {
            const selectedCountry = countries.find(c => c.alpha2 === value);
            setLocalFilters(prev => ({
                ...prev,
                country: value,
                mid: selectedCountry?.mid
            }));
        }
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
                                className="select select-bordered select-sm"
                                value={localFilters.country || ""}
                                onChange={e => handleCountryChange(e.target.value)}
                                disabled={loadingCountries}
                            >
                                <option value="">All countries</option>
                                {countries.map(country => (
                                    <option key={country.name} value={country.name}>
                                        {country.name} ({country.alpha2})
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
                                placeholder="Min length"
                                className="input input-bordered input-sm"
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
                                placeholder="Max length"
                                className="input input-bordered input-sm"
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
                                placeholder="Min Width"
                                className="input input-bordered input-sm"
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
                                placeholder="Max Width"
                                className="input input-bordered input-sm"
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
                                placeholder="Min draft"
                                className="input input-bordered input-sm"
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
                                placeholder="Max draft"
                                className="input input-bordered input-sm"
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