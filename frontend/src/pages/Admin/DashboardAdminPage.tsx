import React from "react";
import {Route, Routes} from "react-router-dom";
import AdminAllUsers from "./AllUsers/AdminAllUsers"
import AdminRequestProperty from "./RequestProperty/AdminRequestProperty"

const DashboardAdminPage: React.FC = () => {
    return (
        <Routes>
            <Route index element={<AdminAllUsers />}></Route>
            <Route path="list-users" element={<AdminAllUsers />}></Route>
            <Route path="request-property" element={<AdminRequestProperty />}></Route>
        </Routes>
    );
};

export default DashboardAdminPage;