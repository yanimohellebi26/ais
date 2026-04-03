import React, { useEffect, useMemo, useState } from "react";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useLoading } from "../../../context/LoadingContext";
import {AnalyticsFilters} from "./interfaces"
import DatePicker from "../../../components/BaseComponents/DatePicker";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { Map as MapLibreMap, Source, Layer } from "@vis.gl/react-maplibre";
import { MapMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MAP_STYLES, DEFAULT_VIEW_STATE_PREVIEW } from "../../Map/constants/mapStyles";
import { createRadiusCircle } from "../../Map/utils/mapGeometry";

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

    const [localFilters, setLocalFilters] = useState<AnalyticsFilters>(filters);
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

    const dateRange: DateRange | undefined = useMemo(() => {
        const from = localFilters.dateFrom ? new Date(localFilters.dateFrom) : undefined;
        const to = localFilters.dateTo ? new Date(localFilters.dateTo) : undefined;
        return from || to ? { from, to } : undefined;
    }, [localFilters.dateFrom, localFilters.dateTo]);

    const handleDateSelect = (value: Date | DateRange | undefined) => {
        const range = value as DateRange | undefined;
        setLocalFilters(prev => ({
            ...prev,
            dateFrom: range?.from ? format(range.from, "yyyy-MM-dd") : undefined,
            dateTo: range?.to ? format(range.to, "yyyy-MM-dd") : undefined,
        }));
    };

    const handleMapClick = (e: MapMouseEvent) => {
        const { lng, lat } = e.lngLat;
        setLocalFilters(prev => ({
            ...prev,
            latitude: Math.round(lat * 1e6) / 1e6,
            longitude: Math.round(lng * 1e6) / 1e6,
        }));
    };

    const hasMarker = localFilters.latitude != null && localFilters.longitude != null;

    const markerGeoJson = useMemo(() => {
        if (!hasMarker) return null;
        return {
            type: "FeatureCollection" as const,
            features: [{
                type: "Feature" as const,
                geometry: {
                    type: "Point" as const,
                    coordinates: [localFilters.longitude!, localFilters.latitude!]
                },
                properties: {}
            }]
        };
    }, [localFilters.latitude, localFilters.longitude]);

    const radiusGeoJson = useMemo(() => {
        if (!hasMarker || !localFilters.radius) return null;
        return createRadiusCircle(
            localFilters.longitude!,
            localFilters.latitude!,
            localFilters.radius / 1000
        );
    }, [localFilters.latitude, localFilters.longitude, localFilters.radius]);


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

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* DATES */}
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Date Range</span>
                                </label>

                                <div className="bg-base-100 border border-base-300 rounded-xl p-3">
                                    <DatePicker
                                        mode="range"
                                        selected={dateRange}
                                        onSelect={handleDateSelect}
                                    />
                                </div>

                                {(localFilters.dateFrom || localFilters.dateTo) && (
                                    <button
                                        className="btn btn-xs btn-ghost mt-2 self-start"
                                        onClick={() => {
                                            handleChange("dateFrom", undefined);
                                            handleChange("dateTo", undefined);
                                        }}
                                    >
                                        Clear dates
                                    </button>
                                )}
                            </div>


                            {/* LOCATION */}
                            <div className="form-control">
                                <div className="flex items-center justify-between">
                                    <label className="label">
                                        <span className="label-text">Location</span>
                                    </label>
                                    <div className="flex items-center gap-2">
                                        {hasMarker && (
                                            <span className="text-xs text-base-content/50">
                                                {localFilters.latitude?.toFixed(4)}, {localFilters.longitude?.toFixed(4)}
                                            </span>
                                        )}
                                        {hasMarker && (
                                            <button
                                                className="btn btn-xs btn-ghost text-error"
                                                onClick={() => {
                                                    handleChange("latitude", undefined);
                                                    handleChange("longitude", undefined);
                                                    handleChange("radius", undefined);
                                                }}
                                            >
                                                Clear
                                            </button>
                                        )}
                                    </div>
                                </div>

                                <div className="mt-2 space-y-2">
                                    <div
                                        className="rounded-xl overflow-hidden border border-base-300"
                                        style={{ height: 250 }}
                                    >
                                        <MapLibreMap
                                            initialViewState={DEFAULT_VIEW_STATE_PREVIEW}
                                            mapStyle={MAP_STYLES.STANDARD}
                                            style={{ width: "100%", height: "100%" }}
                                            onClick={handleMapClick}
                                            cursor="crosshair"
                                        >
                                            {markerGeoJson && (
                                                <Source id="marker" type="geojson" data={markerGeoJson}>
                                                    <Layer
                                                        id="marker-layer"
                                                        type="circle"
                                                        paint={{
                                                            "circle-radius": 7,
                                                            "circle-color": "#ef4444",
                                                            "circle-stroke-width": 2,
                                                            "circle-stroke-color": "#ffffff",
                                                        }}
                                                    />
                                                </Source>
                                            )}

                                            {radiusGeoJson && (
                                                <Source id="radius" type="geojson" data={radiusGeoJson}>
                                                    <Layer
                                                        id="radius-fill"
                                                        type="fill"
                                                        paint={{
                                                            "fill-color": "#3b82f6",
                                                            "fill-opacity": 0.1,
                                                        }}
                                                    />
                                                    <Layer
                                                        id="radius-outline"
                                                        type="line"
                                                        paint={{
                                                            "line-color": "#3b82f6",
                                                            "line-width": 2,
                                                        }}
                                                    />
                                                </Source>
                                            )}
                                        </MapLibreMap>
                                    </div>

                                    {hasMarker && (
                                        <div className="form-control">
                                            <label className="label"><span className="label-text">
                                                    Radius: {localFilters.radius
                                                ? `${(localFilters.radius / 1000).toFixed(0)} km`
                                                : "none"}
                                                </span>
                                            </label>
                                            <input
                                                type="range"
                                                min={5000}
                                                max={1000000}
                                                step={5000}
                                                value={localFilters.radius ?? 0}
                                                className="range range-primary range-sm"
                                                onChange={e => handleChange(
                                                    "radius",
                                                    Number(e.target.value) === 0 ? undefined : Number(e.target.value)
                                                )}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
};

export default TableFilters;