import React, {useEffect, useState} from "react"
import { User } from "./types";
import { useAuth } from "../../../context/AuthContext";
import { toast } from "react-toastify";
import TitleH1 from "../../../components/BaseComponents/TitleH1";
import { useApi } from "../../../utils/api";
import { GenericTable } from "../../../components/BaseComponents/GenericTable";
import Swal from "sweetalert2";
import withReactContent from "sweetalert2-react-content";
import { UpdateUserRequest } from "../../../types";
import Button from "../../../components/BaseComponents/Button";

const MySwal = withReactContent(Swal);

const TableUsers: React.FC = () => {
    const { user } = useAuth();
    const [users, setUsers] = useState<User[]>([]);

    const api = useApi();

    const columns = [
        {id: "id", accessorKey: "id", header: "ID"},
        {id: "username", accessorKey: "username", header: "Username"},
        {id: "email", accessorKey: "email", header: "Email"},
        {id: "role", accessorKey: "role", header: "Role", cell: ({ row } : any) => row.original.role.name},
        {id: "create_at", accessorKey: "created_at", header: "Created At", cell: (info: any) => new Date(info.getValue()).toLocaleDateString()},
        {id: "last_update", accessorKey: "last_update", header: "Last Update", cell: (info: any) => new Date(info.getValue()).toLocaleDateString()},
        {id: "actions", accessorKey: "actions", header: "Actions", cell: ({ row }: any) => (
            <Button onClick={() => handleModification(row.original)}>Edit</Button>
        )}
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

    const handleModification = async (user: User) => {
        const { value: password } = await MySwal.fire({
            title: `Modifications for ${user.username}`,
            input: "password",
            inputLabel: "New Password",
            inputPlaceholder: "Enter new password...",
            showCancelButton: true,
            confirmButtonText: "Save",
            preConfirm: (value) => {
                if (!value || value.length < 8) {
                    Swal.showValidationMessage("Password must be at least 8 characters");
                }
                return value;
            }
        });

        if (password) {
            try {
                const payload: UpdateUserRequest = {
                    id: user.id,
                    password: password
                };

                await api<User>("/api/v1/users", {
                    method: "PUT",
                    headers: {"Content-Type" : "application/json"},
                    body: JSON.stringify(payload)
                });

                toast.success(`User ${user.id} updated successfuly`)
            } catch (error) {
                toast.error("Failed to update the current user")
            }
        }
    }

    return (
        <div>
            <TitleH1>All Users</TitleH1>

            <GenericTable data={users} columns={columns} className="mt-4"/>
        </div>
    );
};

export default TableUsers;