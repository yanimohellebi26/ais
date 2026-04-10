import React, {useMemo} from "react";
import { useVesselTypeStats } from "../../../hooks/useVesselTypeStats";
import {AnalyticsFilters} from "./interfaces";
import { Bar } from "react-chartjs-2";
import { ChartOptions } from "chart.js";

interface Props {
    filters?: AnalyticsFilters;
}

const VesselTypeWidget: React.FC<Props> = ({ filters }) => {
    const { data, loading } = useVesselTypeStats({ filters, topN: 5 });
    const sorted = useMemo(() => {
        if (!data) return [];
        return [...data].sort((a, b) => b.efficiencyKmh - a.efficiencyKmh);
    }, [data]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-[150px]">
                <span className="loading loading-spinner loading-sm" />
            </div>
        );
    }

    if (sorted.length === 0) {
        return (
            <div className="flex justify-center items-center h-[150px] text-sm text-base-content/50">
                No data available
            </div>
        );
    }

    const chartData = {
        labels: sorted.map(d => d.vesselTypeDescription),
        datasets: [
            {
                data: sorted.map(d => d.efficiencyKmh),
                backgroundColor: sorted.map((_, i) =>
                    i === 0 ? "#FF9F40" : "rgba(37, 99, 235, 0.3)"
                ),
            },
        ],
    };

    const options: ChartOptions<"bar"> = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "x",
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const d = sorted[ctx.dataIndex];
                        return `${d.vesselTypeDescription}: ${d.efficiencyKmh} km/h`;
                    },
                },
            },
        },
        scales: {
            x: {
                display: false,
            },
            y: {
                ticks: {
                    display: true,
                    font: { size: 10 },
                },
            },
        },
    };

    return (
        <div className="w-full h-[150px]">
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default VesselTypeWidget;