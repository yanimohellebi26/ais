import React, { useEffect, useState } from "react";
import { Info, Key, Plus, Trash2 } from "lucide-react";
import { useEtlApi } from "../../../hooks/useEtlApi";
import { ApiKey } from "./interfaces";
import { toast } from "react-toastify";
import PasswordInput from "../../../components/BaseComponents/PasswordInput";
import CopyButton from "../../../components/BaseComponents/CopyButton";
import * as sweetalert2 from "sweetalert2";
import Swal from "sweetalert2";

const CreateApiKeys: React.FC = () => {
    const api = useEtlApi();
    const [keys, setKeys] = useState<ApiKey[]>([]);
    const [newUsername, setNewUsername] = useState("");

    // Fetch all API keys
    const fetchApiKeys = async () => {
        try {
            const response = await api("/apiKeys/", {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            });

            const keysArray: ApiKey[] = Object.entries(response.api_keys).map(
                ([key, value]: [string, any]) => ({
                    key,
                    name: value.name,
                    date: new Date(value.created_at),
                })
            );
            setKeys(keysArray);
        } catch (e) {
            toast.error("Failed to fetch API keys");
        }
    };

    useEffect(() => {
        fetchApiKeys();
    }, []);

    // Create new API key
    const handleCreateKey = async () => {
        if (!newUsername.trim()) {
            toast.warning("Please enter a username");
            return;
        }

        try {
            const response = await api("/apiKeys/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newUsername }),
            });

            const newKey: ApiKey = {
                key: response.api_key,
                name: response.name,
                date: new Date(),
            };

            setKeys((prev) => [...prev, newKey]);
            setNewUsername("");
            toast.success(`API key created for ${newKey.name}`);
        } catch (e) {
            toast.error("Failed to create API key");
        }
    };

    // Delete existing API key
    const handleDeleteKey = async (key: string) => {
        const response = await Swal.fire({
            title: "Are you sure?",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, delete it!",
            cancelButtonText: "No, cancel",
        })
        if(!response.isConfirmed) return;

        try {
            const response = await api(`/apiKeys/${key}`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
            });

            if (response.deleted) {
                setKeys((prev) => prev.filter((k) => k.key !== key));
                toast.success("API key deleted successfully");
            } else {
                toast.error("Failed to delete API key");
            }
        } catch (e) {
            toast.error("Error while deleting API key");
        }
    };

    return (
        <div className="rounded-2xl shadow-sm bg-base-100 p-4 border border-accent space-y-4">
            <div className="flex items-center">
                <Key />
                <span className="font-semibold pl-2 mr-2">API Keys Management</span>
            </div>

            <p className="text-base-content/70">
                Create and manage API keys for users accessing the ETL Data platform.
            </p>

            <span className="label font-semibold">New username</span>

            <div className="flex gap-2">
                <input
                    type="text"
                    className="input input-bordered flex-1"
                    placeholder="username"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                />
                <button
                    className="btn btn-soft btn-success"
                    onClick={handleCreateKey}
                >
                    <Plus />
                    Create Key
                </button>
            </div>

            <div>
                {keys.length > 0 ? (
                    <div className="max-h-96 overflow-y-auto">
                        <table className="table table-zebra mt-2">
                            <thead>
                            <tr>
                                <th>Username</th>
                                <th>API Key</th>
                                <th>Created At</th>
                                <th>Actions</th>
                            </tr>
                            </thead>
                            <tbody>
                            {keys.map((k) => (
                                <tr key={k.key}>
                                    <td>{k.name}</td>
                                    <td>
                                        <PasswordInput
                                            id={`apikey-${k.key}`}
                                            value={k.key}
                                            className="max-w-md"
                                        />
                                    </td>
                                    <td>{k.date.toLocaleString()}</td>
                                    <td className="flex gap-2">
                                        <CopyButton targetId={`apikey-${k.key}`} />

                                        <button
                                            className="btn btn-ghost btn-sm text-error hover:bg-error/10"
                                            onClick={() => handleDeleteKey(k.key)}
                                        >
                                            <Trash2 size={18} />
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div>
                        No API keys created yet. Create your first API key by entering a username
                        above.
                    </div>
                )}
            </div>
        </div>
    );
};

export default CreateApiKeys;
