import React, { useEffect, useState, useMemo } from "react";
import {useLocation, useNavigate} from "react-router-dom";
import { useVesselTypeStats } from "../../../hooks/useVesselTypeStats";
import { VesselTypeStat } from "../../../hooks/useVesselTypeStats";
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
    ChartOptions,
    TooltipItem
} from "chart.js";
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

type Metric = "trajectory" | "distance" | "speed" | "avgDistance" | "totalDuration" | "avgDuration" | "efficiency";
type ChartType = "bar" | "radar" | "scatter";

const CHART_LABELS: Record<ChartType, string> = {
    bar: "Classement",
    scatter: "Performance",
    radar: "Profil",
};

const METRIC_LABELS: Record<Metric, string> = {
    trajectory: "Number of Trajectories",
    distance: "Total Distance (km)",
    speed: "Average Speed (km/h)",
    avgDistance: "Average Distance (km)",
    totalDuration: "Total Duration (h)",
    avgDuration: "Average Duration (h)",
    efficiency: "Efficiency (km/h)",
};

const METRIC_ACCESSORS: Record<Metric, (d: VesselTypeStat ) => number> = {
    trajectory: d => d.trajectoryCount,
    distance: d => d.totalDistanceKm,
    speed: d => d.avgSpeedKmh,
    avgDistance: d => d.avgDistanceKm,
    totalDuration: d => d.totalDurationHours,
    avgDuration: d => d.avgDurationHours,
    efficiency: d => d.efficiencyKmh,
};

const HORIZONTAL_METRICS: Metric[] = ["distance", "avgDistance", "totalDuration", "avgDuration"];

const RADAR_COLORS = [
    { border: "#2563eb", background: "rgba(37, 99, 235, 0.15)" },
    { border: "#16a34a", background: "rgba(22, 163, 74, 0.15)" },
    { border: "#dc2626", background: "rgba(220, 38, 38, 0.15)" },
    { border: "#9333ea", background: "rgba(147, 51, 234, 0.15)" },
    { border: "#ea580c", background: "rgba(234, 88, 12, 0.15)" },
];

const VesselTypeStatisticsModule: React.FC<Props> = ({ filters }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters: AnalyticsFilters = useMemo( () =>
        filters || (location.state as any)?.filters || {},
        [filters, location.state]
    );

    const [metric, setMetric] = useState<Metric>("efficiency");
    const [chartType, setChartType] = useState<ChartType>("bar");
    const [topN, setTopN] = useState(10);
    const isSliderDisabled = chartType === "radar";

    useEffect(() => {
        if (chartType !== "bar") {
            setMetric("efficiency");
            if (chartType === "radar") setTopN(5);
            else { setTopN(10); }
        }
    }, [chartType]);

    const { data, loading } = useVesselTypeStats({ filters: initialFilters, topN });

    const metricData = useMemo(() => {
        if (!data) return [];
        return [...data].sort((a, b) => METRIC_ACCESSORS[metric](b) - METRIC_ACCESSORS[metric](a));
    }, [data, metric]);

    const maxTrajectories = useMemo(
        () => Math.max(...metricData.map(d => d.trajectoryCount), 1),
        [metricData]
    );

    const normalizedRadarData = useMemo(() => {
        if (metricData.length === 0) return [];

        const fields: (keyof VesselTypeStat)[] = [
            "trajectoryCount",
            "totalDistanceKm",
            "avgSpeedKmh",
            "avgDistanceKm",
            "totalDurationHours",
            "avgDurationHours",
            "efficiencyKmh",
        ];
        const n = metricData.length;
        const ranks: Record<string, number[]> = {};

        fields.forEach((f) => {
            const indexed = metricData.map((d, idx) => ({
                value: d[f] as number,
                index: idx,
            }));
            indexed.sort((a, b) => a.value - b.value);
            const ranksArray = new Array(n);

            let i = 0;
            while (i < indexed.length) {
                let j = i;
                while (
                    j < indexed.length &&
                    indexed[j].value === indexed[i].value
                    ) {
                    j++;
                }
                const avgRank = (i + j - 1) / 2;
                for (let k = i; k < j; k++) {
                    ranksArray[indexed[k].index] = avgRank;
                }
                i = j;
            }
            ranks[f] = ranksArray;
        });

        return metricData.slice(0, 5).map((_, idx) =>
            fields.map((f) => {
                const rank = ranks[f][idx];
                return n > 1 ? rank / (n - 1) : 1;
            })
        );
    }, [metricData]);

    const backgroundColors = metricData.map((_, index) =>
        index === 0 ? PRIMARY_COLOR : SECONDARY_COLOR
    );

    const chartData = {
        labels: metricData.map(d => d.vesselTypeDescription),
        datasets: [
            {
                label: METRIC_LABELS[metric],
                data: metricData.map(d => METRIC_ACCESSORS[metric](d)),
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
        indexAxis: HORIZONTAL_METRICS.includes(metric) ? "y" : "x",
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx: TooltipItem<"bar">) => {
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
            "Total Distance (km)",
            "Avg Speed (km/h)",
            "Avg Distance (km)",
            "Total Duration (h)",
            "Avg Duration (h)",
            "Efficiency (km/h)",
        ],

        datasets: metricData.slice(0, 5).map((d, idx) => ({
            label: d.vesselTypeDescription,
            data: normalizedRadarData[idx],
            backgroundColor: RADAR_COLORS[idx].background,
            borderColor:  RADAR_COLORS[idx].border,
            borderWidth: idx === 0 ? 2 : 1.5,
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
                    label: (ctx: TooltipItem<"radar">) => {
                        const vessel = metricData[ctx.datasetIndex];
                        if (!vessel) return "";

                        const realValues = [
                            `Trajectories: ${vessel.trajectoryCount}`,
                            `Total Distance: ${vessel.totalDistanceKm} km`,
                            `Avg Speed: ${vessel.avgSpeedKmh} km/h`,
                            `Avg Distance: ${vessel.avgDistanceKm} km`,
                            `Total Duration: ${vessel.totalDurationHours} h`,
                            `Avg Duration: ${vessel.avgDurationHours} h`,
                            `Efficiency: ${vessel.efficiencyKmh} km/h`,
                        ];

                        return realValues[ctx.dataIndex] ?? "";
                    },
                },
            },
        },
        scales: {
            r: {
                beginAtZero: true,
                min: 0,
                max: 1,
                ticks: {
                    display: false,
                },
                pointLabels: {
                    font: {size: 11},
                },
            },
        },
    };

    const scatterData = {
        datasets: [{
            label: "Vessel Types",
            data: metricData.map(d => ({
                x: d.totalDistanceKm,
                y: d.efficiencyKmh,
            })),

            backgroundColor: backgroundColors,
            borderWidth: metricData.map((_, i) => (i === 0 ? 2 : 1)),
            borderColor: metricData.map((_, i) =>
                i === 0 ? "#1e40af" : "rgba(37, 99, 235, 0.8)"
            ),
            pointRadius: metricData.map(d =>
                6 + (d.trajectoryCount / maxTrajectories) * 18
            ),
            pointHoverRadius: metricData.map(d =>
                8 + (d.trajectoryCount / maxTrajectories) * 18
            ),
        }],
    };

    const scatterOptions: ChartOptions<"scatter"> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: (ctx: TooltipItem<"scatter">) => {
                        const d = metricData[ctx.dataIndex];
                        return [
                            d.vesselTypeDescription,
                            `Distance: ${d.totalDistanceKm} km`,
                            `Efficiency: ${d.efficiencyKmh} km/h`,
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
                grid: { color: "rgba(0,0,0,0.05)" },
            },
            y: {
                title: {
                    display: true,
                    text: "Efficiency (km/h)",
                },
                grid: { color: "rgba(0,0,0,0.05)" },
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
                {(["bar", "radar", "scatter"] as ChartType[]).map((type) => (
                    <button
                        key={type}
                        className={`btn btn-sm ${chartType === type ? "btn-primary" : "btn-outline"}`}
                        onClick={() => setChartType(type)}
                    >
                        {type === "bar" && <BarChart3 size={16} />}
                        {type === "radar" && <RadarIcon size={16} />}
                        {type === "scatter" && <ScatterChart size={16} />}
                        {CHART_LABELS[type]}
                    </button>
                ))}
            </div>

            {chartType === "bar" && (
                <div className="flex flex-wrap gap-2 mt-4">
                    {(Object.keys(METRIC_LABELS) as Metric[]).map((m) => (
                        <button
                            key={m}
                            className={`btn btn-sm ${metric === m ? "btn-primary" : "btn-outline"}`}
                            onClick={() => setMetric(m)}
                        >
                            {METRIC_LABELS[m]}
                        </button>
                    ))}
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
                    disabled={isSliderDisabled}
                    className={`range range-sm ${isSliderDisabled ? "range-ghost opacity-40 cursor-not-allowed" : "range-primary"}`}
                    onChange={(e) => !isSliderDisabled && setTopN(Number(e.target.value))}
                />
                <div className="text-xs mt-1 text-gray-500 text-right">
                    {isSliderDisabled
                        ? "Fixed to top 5 in profil mode"
                        : `Top ${topN} vessel types${chartType === "bar" ? ` for ${METRIC_LABELS[metric]}` : ""}`
                    }
                </div>
            </div>

            {loading && (
                <div className="mt-6 text-center">
                    <span className="loading loading-spinner loading-lg"></span>
                </div>
            )}
            {!loading && metricData.length === 0 && (
                <div className="mt-6 text-center text-gray-500">
                    No data available for the selected filters.
                </div>
            )}

            {!loading && metricData.length > 0 && (
                <div className="card bg-base-100 shadow p-6 h-[450px]">
                    <div className="w-full h-full">
                        {chartType === "bar" && <Bar key={metric} data={chartData} options={options} />}
                        {chartType === "radar" && <Radar data={radarData} options={radarOptions} />}
                        {chartType === "scatter" && <Scatter data={scatterData} options={scatterOptions} />}
                    </div>
                </div>
            )}
        </>
    );
};

export default VesselTypeStatisticsModule;