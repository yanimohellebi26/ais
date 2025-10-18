import React from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import TableUsers from "./TableUsers";

const AdminAllUsers: React.FC = () => {
    return (
        <>
            <Breadcrumbs />
            <TableUsers />
        </>
    );
};

export default AdminAllUsers;