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
        let newPassword = "";
        let newRole = user.role;
        
        const result = await MySwal.fire({
            title: `Modifications for ${user.username}`,
            html: (
                <div className="flex flex-col gap-2">
                    <input
                        type="password"
                        className="swal2-input"
                        placeholder="New password (optional)"
                        onChange={(e) => (newPassword = e.target.value)}
                    />
                    <select
                        className="swal2-select"
                        defaultValue={newRole}
                        onChange={(e) => (newRole = e.target.value)}
                    >
                        <option value="ADMIN">Admin</option>
                        <option value="OWNER">Ship Owner</option>
                        <option value="MARITIME_EXPERT">Maritime Expert</option>
                        <option value="CAPTAIN">Captain</option>
                        <option value="FINANCIAL_ANALYST">Financial Analyst</option>
                    </select>
                </div>
            ),
            showCancelButton: true,
            focusConfirm: false,
            confirmButtonText: "Save",
            preConfirm: () => {
                if (newPassword) {
                    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
                    if (!regex.test(newPassword)) {
                        Swal.showValidationMessage(
                            "Password must be at least 8 characters long and include upper, lower, digit, and special character"
                        );
                    }
                }
                return { password: newPassword || null, role: newRole };
            },
        });

        if (result.isConfirmed && result.value) {
            try {
                const payload: UpdateUserRequest = {
                    id: user.id,
                    password: result.value.password,
                    role: result.value.role
                };

                await api<User>("/api/v1/users", {
                    method: "PUT",
                    headers: {"Content-Type" : "application/json"},
                    body: JSON.stringify(payload)
                });

                toast.success(`User ${user.id} updated successfuly`)

                setUsers( prev => 
                    prev.map( u => 
                        u.id === user.id ? {...u, role: result.value?.role ?? u.role } : u
                    )
                )
            } catch (error) {
                toast.error("Failed to update the current user")
            }
        }
    }

    const columns = [
        {id: "id", accessorKey: "id", header: "ID"},
        {id: "username", accessorKey: "username", header: "Username"},
        {id: "email", accessorKey: "email", header: "Email"},
        {id: "role", accessorKey: "role", header: "Role", cell: ({ row } : any) => row.original.role},
        {id: "create_at", accessorKey: "created_at", header: "Created At", cell: (info: any) => new Date(info.getValue()).toLocaleDateString()},
        {id: "last_update", accessorKey: "last_update", header: "Last Update", cell: (info: any) => new Date(info.getValue()).toLocaleDateString()},
        {id: "actions", accessorKey: "actions", header: "Actions", cell: ({ row }: any) => (
            <Button onClick={() => handleModification(row.original)}>Edit</Button>
        )}
    ]

    return (
        <div>
            <TitleH1>All Users</TitleH1>

            <GenericTable data={users} columns={columns} className="mt-4"/>
        </div>
    );
};

export default TableUsers;