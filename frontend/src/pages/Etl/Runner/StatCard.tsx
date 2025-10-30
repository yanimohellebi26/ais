import React, {useState} from "react";
import {ArrowLeftRight, ArrowRightLeft} from "lucide-react";

interface StatCardProps {
    titleTotal: string;
    titleToday: string;
    totalValue: number | string;
    todayValue: number | string;
    color?: "primary" | "success" | "error" | "warning";
}

const StatCard: React.FC<StatCardProps> = ({ titleTotal, titleToday, totalValue, todayValue, color = "primary" }) => {
    const [showToday, setShowToday] = useState(false);

    return (
        <div className="carousel-item rounded-box shadow-sm bg-base-100 p-6 w-50 flex flex-col items-center">
            <div className="flex items-center gap-2">
                <h2 className="text-base-content/60">{showToday ? titleToday : titleTotal}</h2>
                <div className={`badge badge-soft badge-${color}`}>
                    {showToday ? todayValue : totalValue}
                </div>
            </div>
            <label className="swap cursor-pointer mt-2" >
                <input type="checkbox" onClick={() => setShowToday(!showToday)}/>
                <ArrowLeftRight className="swap-off" />
                <ArrowRightLeft className="swap-on" />
            </label>
        </div>
    );
};

export default StatCard;