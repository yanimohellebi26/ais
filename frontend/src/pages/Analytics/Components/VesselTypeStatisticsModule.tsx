import React, { useEffect, useState, useMemo } from "react";
import {useLocation, useNavigate} from "react-router-dom";
import { useVesselTypeStats } from "../../../hooks/useVesselTypeStats";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    RadialLinearScale,
    PointElement,
    LineElement,
} from "chart.js";
import type { ChartOptions } from "chart.js";
import { Bar, Radar, Scatter } from "react-chartjs-2";
import {ArrowLeft, BarChart3, RadarIcon, ScatterChart} from "lucide-react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import {AnalyticsFilters} from "./interfaces";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, RadialLinearScale, PointElement, LineElement);

interface Props {
    filters?: AnalyticsFilters;
}

const PRIMARY_COLOR = "#FF9F40";
const SECONDARY_COLOR = "rgba(37, 99, 235, 0.3)";

const TOP_N_BY_METRIC = {
    trajectory: 15,
    distance: 10,
    speed: 5,
};

const VesselTypeStatisticsModule: React.FC<Props> = ({ filters }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters: AnalyticsFilters = filters || (location.state as any)?.filters || {};

    const [metric, setMetric] = useState<"trajectory" | "distance" | "speed">("trajectory");
    const [chartType, setChartType] = useState<"bar" | "radar" | "scatter">("bar");
    const [topN, setTopN] = useState(TOP_N_BY_METRIC[metric]);

    useEffect(() => {
        if (chartType === "bar") {
            setTopN(TOP_N_BY_METRIC[metric]);
        } else {
            setTopN(10);
        }
    }, [metric, chartType]);

    useEffect(() => {
        if (chartType !== "bar") {
            setMetric("trajectory");
        }
    }, [chartType]);

    const { data, loading } = useVesselTypeStats({ filters: initialFilters, topN });

    const metricData = useMemo(() => {
        let sorted = [...data];

        if (metric === "trajectory") {
            sorted.sort((a, b) => b.trajectoryCount - a.trajectoryCount);
        } else if (metric === "distance") {
            sorted.sort((a, b) => b.totalDistanceKm - a.totalDistanceKm);
        } else {
            sorted.sort((a, b) => b.averageSpeedKmh - a.averageSpeedKmh);
        }
        return sorted;
    }, [data, metric]);

    const backgroundColors = metricData.map((_, index) =>
        index === 0 ? PRIMARY_COLOR : SECONDARY_COLOR
    );

    const chartData = {
        labels: metricData.map(d => d.vesselTypeDescription),
        datasets: [
            {
                label:
                    metric === "trajectory"
                        ? "Number of Trajectories"
                        : metric === "distance"
                            ? "Total Distance (km)"
                            : "Average Speed (km/h)",

                data: metricData.map(d =>
                    metric === "trajectory"
                        ? d.trajectoryCount
                        : metric === "distance"
                            ? d.totalDistanceKm
                            : d.averageSpeedKmh
                ),

                backgroundColor: backgroundColors,

                borderWidth: metricData.map((_, i) => (i === 0 ? 2 : 0)),
                borderColor: metricData.map((_, i) =>
                    i === 0 ? "#1e40af" : "transparent"
                ),
            },
        ],
    };

    const options: ChartOptions<"bar"> = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: metric === "distance" ? "y" : "x",
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx: any) => {
                        const item = metricData[ctx.dataIndex];
                        const value = ctx.raw;

                        return [
                            `Type: ${item.vesselTypeDescription}`,
                            `Group: ${item.vesselGroup}`,
                            `${ctx.dataset.label}: ${value}`,
                        ];
                    },
                },
            },
        },
    };

    const radarData = {
        labels: [
            "Trajectories",
            "Distance (km)",
            "Avg Speed (km/h)",
        ],

        datasets: metricData.slice(0, 6).map((d, idx) => ({
            label: d.vesselTypeDescription,

            data: [
                d.trajectoryCount,
                d.totalDistanceKm,
                d.averageSpeedKmh,
            ],

            backgroundColor: `rgba(37, 99, 235, 0.1)`,
            borderColor: idx === 0 ? "#2563eb" : "#94a3b8",
            borderWidth: idx === 0 ? 2 : 1,
        })),
    };

    const radarOptions: ChartOptions<"radar"> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: "top",
            },
            tooltip: {
                callbacks: {
                    label: (ctx: any) =>
                        `${ctx.dataset.label}: ${ctx.raw}`,
                },
            },
        },
        scales: {
            r: {
                beginAtZero: true,
            },
        },
    };

    const scatterData = {
        datasets: [{
            label: "Vessel Types",
            data: metricData.map(d => ({
                x: d.totalDistanceKm,
                y: d.averageSpeedKmh,
            })),

            backgroundColor: "#2563eb",
        }],
    };

    const scatterOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx: any) => {
                        const d = metricData[ctx.dataIndex];
                        return [
                            d.vesselTypeDescription,
                            `Distance: ${d.totalDistanceKm} km`,
                            `Speed: ${d.averageSpeedKmh} km/h`,
                            `Trajectories: ${d.trajectoryCount}`,
                        ];
                    },
                },
            },
        },

        scales: {
            x: {
                title: {
                    display: true,
                    text: "Total Distance (km)",
                },
            },
            y: {
                title: {
                    display: true,
                    text: "Average Speed (km/h)",
                },
            },
        },
    };

    return (
        <>
            <Breadcrumbs />
            <div className="flex gap-4 mt-4">
                <button className="btn btn-sm btn-outline"
                        onClick={() => navigate("/dashboard/analytics", { state: { filters: initialFilters } })}
                >
                    <ArrowLeft />
                    Back
                </button>
                <h1 className="text-2xl font-semibold pb-4">Vessel Type Statistics</h1>
            </div>

            <div className="flex gap-2 mt-4">
                <button
                    className={`btn btn-sm ${chartType === "bar" ? "btn-primary" : "btn-outline"}`}
                    onClick={() => setChartType("bar")}
                >
                    <BarChart3 size={16} />
                    Bar
                </button>

                <button
                    className={`btn btn-sm ${chartType === "radar" ? "btn-primary" : "btn-outline"}`}
                    onClick={() => setChartType("radar")}
                >
                    <RadarIcon size={16} />
                    Radar
                </button>

                <button
                    className={`btn btn-sm ${chartType === "scatter" ? "btn-primary" : "btn-outline"}`}
                    onClick={() => setChartType("scatter")}
                >
                    <ScatterChart size={16} />
                    Scatter
                </button>
            </div>

            {chartType === "bar" && (
                <div className="flex gap-2 mt-4">
                    <button
                        className={`btn btn-sm ${metric === "trajectory" ? "btn-primary" : "btn-outline"}`}
                        onClick={() => setMetric("trajectory")}
                    >
                        Trajectories
                    </button>
                    <button
                        className={`btn btn-sm ${metric === "distance" ? "btn-primary" : "btn-outline"}`}
                        onClick={() => setMetric("distance")}
                    >
                        Distance
                    </button>
                    <button
                        className={`btn btn-sm ${metric === "speed" ? "btn-primary" : "btn-outline"}`}
                        onClick={() => setMetric("speed")}
                    >
                        Speed
                    </button>
                </div>
            )}

            <div className="form-control w-64 mt-4 mb-4">
                <label className="label">
                    <span className="label-text font-medium">Top N vessel types</span>
                </label>
                <input
                    type="range"
                    min={5}
                    max={20}
                    step={5}
                    value={topN}
                    className="range range-primary range-sm"
                    onChange={(e) => setTopN(Number(e.target.value))}
                />
                <div className="text-xs mt-1 text-gray-500 text-right">
                    Top {topN} vessel types
                    {chartType === "bar" && ` for ${metric}`}
                </div>
            </div>

            {loading && (
                <div className="mt-6 text-center">
                    <span className="loading loading-spinner loading-lg"></span>
                </div>
            )}
            {!loading && data.length === 0 && (
                <div className="mt-6 text-center text-gray-500">
                    No data available for the selected filters.
                </div>
            )}

            {!loading && data.length > 0 && (
                <div className="card bg-base-100 shadow p-6 h-[450px]">
                    <div className="w-full h-full">
                        {chartType === "bar" && (
                            <Bar data={chartData} options={options} />
                        )}

                        {chartType === "radar" && (
                            <Radar data={radarData} options={radarOptions} />
                        )}

                        {chartType === "scatter" && (
                            <Scatter data={scatterData} options={scatterOptions} />
                        )}
                    </div>
                </div>
            )}
        </>
    );
};

export default VesselTypeStatisticsModule;