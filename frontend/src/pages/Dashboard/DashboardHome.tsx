import React from "react";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import Breadcrumbs from "../../components/BaseComponents/Breadcrumbs";
import {useCurrentUser} from "../../hooks/useCurrentUser";
import DashletUserInfo from "./Dashlets/DashletUserInfo";

const DashboardHome: React.FC = () => {
    const {userData} = useCurrentUser();

    return (
        <div>
            <Breadcrumbs/>
            <TitleH1 className="text-2xl font-bold mb-4">Welcome in, {userData?.username}</TitleH1>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl mx-auto p-4">
                <DashletUserInfo/>
            </div>
        </div>
    );
};

export default DashboardHome;
