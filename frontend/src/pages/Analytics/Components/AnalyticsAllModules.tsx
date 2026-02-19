import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";

const AnalyticsAllModules: React.FC = () => {
    return (
        <>
            <Breadcrumbs/>
            <div className="flex justify-between mb-6">
                <h1 className="text-2xl font-semibold mr-4">Analytics</h1>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {/* les modules ici */}
            </div>

        </>
    );
};

export default AnalyticsAllModules;