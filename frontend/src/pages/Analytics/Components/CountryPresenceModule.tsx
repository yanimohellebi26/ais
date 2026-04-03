import React, { useState } from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import { ArrowLeft } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useCountryPresence } from "../../../hooks/useCountryPresence";
import { AnalyticsFilters } from "./interfaces";
import { Bar } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
    Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

interface Props {
    filters?: AnalyticsFilters;
}

const CountryPresenceModule: React.FC<Props> = ({ filters }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const initialFilters: AnalyticsFilters = filters || (location.state as any)?.filters || {};

    const [topN, setTopN] = useState(10);
    const { data, loading } = useCountryPresence({ filters: initialFilters, topN });

    const chartData = {
        labels: data.map((d) => d.countryName),
        datasets: [
            {
                label: "Vessels",
                data: data.map((d) => d.vesselCount),
                backgroundColor: "rgba(99, 102, 241, 0.7)",
                borderColor: "rgba(99, 102, 241, 1)",
                borderWidth: 1,
                borderRadius: 4,
            },
        ],
    };

    const chartOptions = {
        indexAxis: "y" as const,
        responsive: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx: any) => ` ${ctx.parsed.x} vessel(s)`,
                },
            },
        },
        scales: {
            x: { beginAtZero: true, ticks: { precision: 0 } },
        },
    };

    return (
        <>
            <Breadcrumbs />
            <div className="flex gap-4 mt-4 mb-6">
                <button
                    className="btn btn-sm btn-outline"
                    onClick={() => navigate("/dashboard/analytics", { state: { filters: initialFilters } })}
                >
                    <ArrowLeft />
                    Back
                </button>
                <h1 className="text-2xl font-semibold">Country Presence</h1>
            </div>

            <div className="card bg-base-100 rounded-2xl shadow-sm p-6">

                <div className="form-control w-64 mb-6">
                    <label className="label">
                        <span className="label-text font-medium">Top N countries</span>
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
                        Current value: <span className="font-semibold">Top {topN}</span>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <span className="loading loading-spinner loading-md" />
                    </div>
                ) : data.length === 0 ? (
                    <div className="flex justify-center items-center h-64 text-base-content/50">
                        No data available for the selected filters
                    </div>
                ) : (
                    <div className="flex flex-col lg:flex-row gap-8">
                        <div className="flex-1">
                            <Bar data={chartData} options={chartOptions} />
                        </div>
                        <div className="w-full lg:w-72 shrink-0">
                            <table className="table table-sm w-full">
                                <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Country</th>
                                    <th>Code</th>
                                    <th className="text-right">Vessels</th>
                                </tr>
                                </thead>
                                <tbody>
                                {data.map((item, index) => (
                                    <tr key={item.alpha2} className="hover">
                                        <td className="text-base-content/50">{index + 1}</td>
                                        <td className="font-medium">{item.countryName}</td>
                                        <td>
                                                <span className="badge badge-ghost badge-sm">
                                                    {item.alpha2}
                                                </span>
                                        </td>
                                        <td className="text-right font-semibold">{item.vesselCount}</td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default CountryPresenceModule;