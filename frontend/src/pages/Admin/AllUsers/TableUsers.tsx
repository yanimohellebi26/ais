import React, {useEffect, useState} from "react"
import { User } from "./types";
import { useAuth } from "../../../context/AuthContext";
import { toast } from "react-toastify";
import TitleH1 from "../../../components/BaseComponents/TitleH1";
import { useApi } from "../../../hooks/useApi";
import { GenericTable } from "../../../components/BaseComponents/GenericTable";
import Swal from "sweetalert2";
import withReactContent from "sweetalert2-react-content";
import { UpdateUserRequest } from "../../../types";
import Button from "../../../components/BaseComponents/Button";
import { jwtDecode } from "jwt-decode";

const MySwal = withReactContent(Swal);

interface TokenPayload {
    id?: number;
    role?: string;
    email?: string;
    [key: string]: any;
}

const getCurrentUserId = (token: string | null): number | undefined => {
    if (!token) return undefined;
    try {
        const decoded = jwtDecode<TokenPayload>(token);
        return decoded.id;
    } catch (error) {
        return undefined;
    }
}

const TableUsers: React.FC = () => {
    const { user } = useAuth();
    const [users, setUsers] = useState<User[]>([]);

    const api = useApi();
    
    const currentUserId = getCurrentUserId(user.token);

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

    const handleModification = async (editedUser: User) => {
        
        let newPassword = "";
        let newRole = editedUser.role;
        const isSelf = currentUserId === editedUser.id;
        
        const result = await MySwal.fire({
            title: `Modifications for ${editedUser.username}`,
            html: (
                <div className="flex flex-col gap-2">
                    <input
                        type="password"
                        className="input input-bordered w-full text-base-content"
                        placeholder="New password (optional)"
                        onChange={(e) => (newPassword = e.target.value)}
                    />
                    <select
                        className="select select-bordered w-full text-base-content bg-base-200"
                        defaultValue={newRole}
                        onChange={(e) => (newRole = e.target.value)}
                        disabled={isSelf}
                    >
                        <option value="ADMIN">Admin</option>
                        <option value="OWNER">Ship Owner</option>
                        <option value="MARITIME_EXPERT">Maritime Expert</option>
                        <option value="CAPTAIN">Captain</option>
                        <option value="FINANCIAL_ANALYST">Financial Analyst</option>
                    </select>
                    {
                        isSelf && (
                            <small className="text-gray-500">
                                You can't change your own role
                            </small>
                        )
                    }
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
                    id: editedUser.id,
                    password: result.value.password,
                    role: isSelf ? editedUser.role : result.value.role
                };

                await api<User>("/api/v1/users", {
                    method: "PUT",
                    headers: {"Content-Type" : "application/json"},
                    body: JSON.stringify(payload)
                });

                toast.success(`User ${editedUser.id} updated successfuly`)

                setUsers( prev => 
                    prev.map( u => 
                        u.id === editedUser.id ? {...u, role: isSelf ? u.role : result.value.role } : u
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
            <Button className="btn btn-sm" onClick={() => handleModification(row.original)}>Edit</Button>
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