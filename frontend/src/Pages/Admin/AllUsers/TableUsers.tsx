import React, {useEffect, useState} from "react"
import { User } from "./types";
import { useAuth } from "../../../context/AuthContext";
import { toast } from "react-toastify";
import TitleH1 from "../../../components/BaseComponents/TitleH1";
import { useApi } from "../../../utils/api";
import { GenericTable } from "../../../components/BaseComponents/GenericTable";

const TableUsers: React.FC = () => {
    const { user } = useAuth();
    const [users, setUsers] = useState<User[]>([]);

    const api = useApi();

    const columns = [
        {id: "id", accessorKey: "id", header: "ID"},
        {id: "username", accessorKey: "username", header: "Username"},
        {id: "email", accessorKey: "email", header: "Email"},
        {id: "role", accessorKey: "role", header: "Role"},
        {id: "create_at", accessorKey: "created_at", header: "Created At", cell: (info: any) => new Date(info.getValue()).toLocaleDateString()},
        {id: "last_update", accessorKey: "last_update", header: "Last Update", cell: (info: any) => new Date(info.getValue()).toLocaleDateString()}
    ]

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await api<User[]>("/api/v1/users");
                setUsers(data);

            } catch(error) {
                toast.error("Error while displaying all the users");
            }
        };

        fetchData();
    }, [user.token]);

    return (
        <div>
            <TitleH1>All Users</TitleH1>

            <GenericTable data={users} columns={columns} className="mt-4"/>
        </div>
    );
};

export default TableUsers;