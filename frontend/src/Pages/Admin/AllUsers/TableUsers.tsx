import React, {useEffect, useState} from "react"
import { User } from "./types";
import { useAuth } from "../../../context/AuthContext";
import { toast } from "react-toastify";
import TitleH1 from "../../../components/BaseComponents/TitleH1";
import { useApi } from "../../../utils/api";

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


    return (
        <div>
            <TitleH1>All Users</TitleH1>

            <table className="min-w-full border border-gray-300 rounded-lg">
                <thead className="bg-gray-100">
                <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Username</th>
                    <th className="px-4 py-2 text-left">Email</th>
                    <th className="px-4 py-2 text-left">Role</th>
                    <th className="px-4 py-2 text-left">Created At</th>
                    <th className="px-4 py-2 text-left">Last Update</th>
                </tr>
                </thead>
                <tbody>
                {users.map((u) => (
                    <tr key={u.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2">{u.id}</td>
                    <td className="px-4 py-2">{u.username}</td>
                    <td className="px-4 py-2">{u.email}</td>
                    <td className="px-4 py-2">{u.role}</td>
                    <td className="px-4 py-2">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-2">{new Date(u.last_update).toLocaleDateString()}</td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
};

export default TableUsers;