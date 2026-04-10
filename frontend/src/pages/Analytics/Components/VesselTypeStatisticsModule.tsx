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
} from "chart.js";
import { Bar } from "react-chartjs-2";
import {ArrowLeft} from "lucide-react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import {AnalyticsFilters} from "./interfaces";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

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
    const [topN, setTopN] = useState(TOP_N_BY_METRIC[metric]);

    useEffect(() => {
        setTopN(TOP_N_BY_METRIC[metric]);
    }, [metric]);

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

    const indexAxis: "x" | "y" =
        metric === "distance" ? "y" : "x";

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis,
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

            <div className="flex gap-2">
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
                    Top {topN} vessel types for {metric}
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
                <div className="mt-6">
                    <div className="card bg-base-100 shadow p-6 h-[450px]">
                        <Bar data={chartData} options={options} />
                    </div>
                </div>
            )}
        </>
    );
};

export default VesselTypeStatisticsModule;