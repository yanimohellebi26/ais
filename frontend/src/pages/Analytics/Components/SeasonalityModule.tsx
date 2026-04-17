import React, { useEffect, useState, useMemo } from "react";
import {useLocation, useNavigate} from "react-router-dom";
import { useSeasonality, Granularity } from "../../../hooks/useSeasonality";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ChartOptions,
    TooltipItem,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { ArrowLeft } from "lucide-react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import { AnalyticsFilters } from "./interfaces";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const granularityOptions: Granularity[] = [
    "AUTO",
    "HOUR",
    "DAY",
    "WEEK",
    "MONTH",
];

const GRANULARITY_LABELS: Record<Exclude<Granularity, "AUTO">, string> = {
    HOUR: "By Hour",
    DAY: "By Day",
    WEEK: "By Week",
    MONTH: "By Month",
};

const MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

interface Props {
    filters?: AnalyticsFilters;
}

const SeasonalityModule: React.FC<Props> = ({ filters }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters: AnalyticsFilters = useMemo( () =>
            filters || (location.state as any)?.filters || {},
        [filters, location.state]
    );

    const hasDateRange = !!(initialFilters.dateFrom || initialFilters.dateTo);

    const [granularity, setGranularity] = useState<Granularity>("AUTO");
    const [year, setYear] = useState<number | undefined>(undefined);

    const { data, loading } = useSeasonality({ filters: initialFilters, granularity, year,});

    const latestYear = useMemo(() => {
        if (!data.length) return undefined;
        return data[0].year ?? undefined;
    }, [data]);

    const inputYear = year ?? latestYear ?? new Date().getFullYear();

    useEffect(() => {
        if (!year && latestYear) {
            setYear(latestYear);
        }
    }, [latestYear]);

    const formatShortDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "short",
        });
    };

    const effectiveGranularity = granularity === "AUTO" ? data[0]?.granularity ?? "DAY" : granularity;
    const selectedGranularity: Granularity = granularity === "AUTO" ? effectiveGranularity : granularity;

    const availableGranularities = useMemo((): Granularity[] => {
        if (!hasDateRange) return [];

        const from = initialFilters.dateFrom ? new Date(initialFilters.dateFrom) : new Date();
        const to = initialFilters.dateTo ? new Date(initialFilters.dateTo) : from;

        const days = Math.round((to.getTime() - from.getTime()) / 86_400_000);

        const options: Granularity[] = [];

        if (days === 0) {
            options.push("HOUR");
            return options;
        }
        if (days <= 90) options.push("DAY");
        if (days <= 365) options.push("WEEK");
        options.push("MONTH");

        return options;
    }, [initialFilters]);

    const labels = useMemo(() => {
        if (!data.length) return [];
        switch (effectiveGranularity) {
            case "HOUR":
                return data.map(d => `${String(d.value).padStart(2, "0")}h`);
            case "MONTH":
                return data.map(d =>
                    d.date
                        ? `${MONTH_NAMES[new Date(d.date).getMonth()]} ${d.year}`
                        : MONTH_NAMES[(d.value ?? 1) - 1]
                );
            case "WEEK":
                return data.map(d =>
                    d.date && d.endDate
                        ? `${formatShortDate(d.date).replace(" ", " ")}–${formatShortDate(d.endDate)}`
                        : d.date ?? ""
                );
            case "DAY":
                return data.map(d =>
                    d.date ? formatShortDate(d.date) : ""
                );
            default:
                return data.map((_, i) => String(i));
        }
    }, [data, effectiveGranularity]);

    const chartData = {
        labels,
        datasets: [{
            label: "Trajectories",
            data: data.map(d => d.trajectoryCount),
            backgroundColor: "rgba(37, 99, 235, 0.1)",
            borderColor: "#2563eb",
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
            fill: true,
            tension: 0.3,
        }],
    };

    const options: ChartOptions<"line"> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    title: (items: TooltipItem<"line">[]) => items[0].label,
                    label: (ctx: TooltipItem<"line">) => {
                        const d = data[ctx.dataIndex];
                        const lines = [`Trajectories: ${d.trajectoryCount}`];
                        if (d.date && d.endDate) lines.push(`Period: ${d.date} → ${d.endDate}`);
                        else if (d.date)         lines.push(`Date: ${d.date}`);
                        return lines;
                    },
                },
            },
        },
        scales: {
            x: {
                grid: { color: "rgba(0,0,0,0.05)" },
                ticks: { maxRotation: 0, autoSkip: true,},
            },
            y: {
                beginAtZero: true,
                grid: { color: "rgba(0,0,0,0.05)" },
                title: { display: true, text: "Number of trajectories" },
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
                <h1 className="text-2xl font-semibold pb-4">Seasonality</h1>
            </div>

            {!hasDateRange && (
                <div className="flex items-center gap-3 mt-4">
                    <span className="text-sm font-medium">Year</span>
                    <input
                        type="number"
                        className="input input-sm input-bordered w-28"
                        value={inputYear}
                        min={2000}
                        max={new Date().getFullYear()}
                        onChange={e => setYear(Number(e.target.value))}
                    />
                </div>
            )}

            {hasDateRange && availableGranularities.length > 0 && (
                <div className="flex items-center gap-3 mt-4">
                    <span className="text-sm font-medium">Display by</span>
                    <div className="flex gap-2">
                        {granularityOptions.map((g) => (
                            <button
                                key={g}
                                className={`btn btn-sm ${
                                    selectedGranularity === g ? "btn-primary" : "btn-outline"
                                }`}
                                disabled={!availableGranularities.includes(g) && g !== "AUTO"}
                                onClick={() => {
                                    if (g === "AUTO") return setGranularity("AUTO");
                                    if (availableGranularities.includes(g)) setGranularity(g);
                                }}
                            >
                                {g === "AUTO" ? "Auto" : GRANULARITY_LABELS[g]}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {loading && (
                <div className="mt-6 text-center">
                    <span className="loading loading-spinner loading-lg" />
                </div>
            )}

            {!loading && data.length === 0 && (
                <div className="mt-6 text-center text-gray-500">
                    No data available for the selected filters.
                </div>
            )}

            {!loading && data.length > 0 && (
                <div className="card bg-base-100 shadow p-6 mt-4 h-[450px]">
                    <div className="w-full h-full">
                        <Line data={chartData} options={options} />
                    </div>
                </div>
            )}
        </>
    );
};

export default SeasonalityModule;