import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

const MapFilterDrawer: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const [filter, setFilter] = useState({
        type: "all",
        radius: 5,
    });

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
        const { name, value } = e.target;
        setFilter(prev => ({ ...prev, [name]: value }));
    };

    return (
        <aside
            className={`z-10 fixed top-0 right-0 h-full bg-base-100 shadow-lg transition-all duration-300 flex flex-col ${
                collapsed ? "w-16" : "w-64"
            }`}
        >
            <div className="flex items-center justify-between p-4 border-b border-base-300">
                {!collapsed && <h2 className="text-lg font-semibold">Filtres Map</h2>}
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="btn btn-ghost btn-sm"
                >
                    {collapsed ? <ChevronLeft /> : <ChevronRight />}
                </button>
            </div>

            {!collapsed && (
                <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto">
                    <div>
                        <label className="block mb-1">Type</label>
                        <select
                            name="type"
                            value={filter.type}
                            onChange={handleChange}
                            className="input input-bordered w-full"
                        >
                            <option value="all">Tous</option>
                            <option value="restaurant">Restaurant</option>
                            <option value="park">Parc</option>
                            <option value="museum">Musée</option>
                        </select>
                    </div>

                    <div>
                        <label className="block mb-1">Rayon (km)</label>
                        <input
                            type="number"
                            name="radius"
                            value={filter.radius}
                            onChange={handleChange}
                            className="input input-bordered w-full"
                            min={1}
                            max={50}
                        />
                    </div>

                    <button
                        className="btn btn-primary mt-4"
                        onClick={() => console.log(filter)}
                    >
                        Appliquer
                    </button>
                </div>
            )}
        </aside>
    );
};

export default MapFilterDrawer;
