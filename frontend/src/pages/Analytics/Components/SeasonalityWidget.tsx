import React, {useMemo} from "react";
import { useSeasonality } from "../../../hooks/useSeasonality";
import {AnalyticsFilters} from "./interfaces";
import { Line } from "react-chartjs-2";
import { ChartOptions } from "chart.js";

const MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

interface Props {
    filters?: AnalyticsFilters;
}

const SeasonalityMonthlyLineWidget: React.FC<Props> = ({ filters }) => {
    const { data, loading } = useSeasonality({ filters, granularity: "MONTH", });

    const latestYear = useMemo(() => {
        if (!data?.length) return new Date().getFullYear();
        return data[0]?.year ?? new Date().getFullYear();
    }, [data]);

    const yearData = useMemo(() => {
        if (!data?.length) return [];
        return data.filter(d => d.year === latestYear);
    }, [data, latestYear]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-[150px]">
                <span className="loading loading-spinner loading-sm" />
            </div>
        );
    }

    if (!yearData.length) {
        return (
            <div className="flex justify-center items-center h-[150px] text-sm text-base-content/50">
                No data available
            </div>
        );
    }

    const chartData = {
        labels: yearData.map(d =>
            d.value ? MONTH_NAMES[d.value - 1] : ""
        ),
        datasets: [
            {
                data: yearData.map(d => d.trajectoryCount),
                borderColor: "#2563eb",
                backgroundColor: "rgba(37, 99, 235, 0.1)",
                fill: true,
                tension: 0.35,
                pointRadius: 3,
                pointHoverRadius: 5,
            },
        ],
    };

    const options: ChartOptions<"line"> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const d = yearData[ctx.dataIndex];
                        return `${MONTH_NAMES[(d.value ?? 1) - 1]}: ${d.trajectoryCount}`;
                    },
                },
            },
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: {
                    font: { size: 10 },
                },
            },
            y: {
                display: false,
                beginAtZero: true,
            },
        },
    };

    return (
        <div className="w-full h-[150px]">
            <Line data={chartData} options={options} />
        </div>
    );
};

export default SeasonalityMonthlyLineWidget;