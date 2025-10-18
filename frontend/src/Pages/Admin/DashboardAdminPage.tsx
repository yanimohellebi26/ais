import React from "react";
import {Route, Routes} from "react-router-dom";
import AdminAllUsers from "./AllUsers/AdminAllUsers"

const DashboardAdminPage: React.FC = () => {
    return (
        <Routes>
            <Route index element={<AdminAllUsers />}></Route>
        </Routes>
    );
};

export default DashboardAdminPage;