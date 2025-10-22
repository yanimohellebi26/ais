import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useApi } from "./useApi";
import type { UserAccount } from "../types";
import {useLoading} from "../context/LoadingContext";
import {toast} from "react-toastify";

export const useCurrentUser = () => {
    const { user } = useAuth();
    const api = useApi();
    const { setLoading} = useLoading();

    const [userData, setUserData] = useState<UserAccount | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchUser = async () => {
            if (!user?.id) return;

            setLoading(true);
            setError(null);

            try {
                const data = await api<UserAccount>(`/api/v1/users/${user.id}`);
                setUserData(data);
            } catch (err: any) {
                toast.error(err.message || "Error while retrieving user data");
                setError(err.message || "Error while retrieving your data");
            } finally {
                setLoading(false);
            }
        };

        fetchUser();
    }, [user?.id]);

    return { userData, error};
};
