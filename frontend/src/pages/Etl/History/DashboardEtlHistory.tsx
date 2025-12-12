import React, {useEffect, useState} from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import AlertApiKey from "../AlertApiKey";
import {useEtlApi} from "../../../hooks/useEtlApi";
import {toast} from "react-toastify";
import TasksHistory from "./TasksHistory";
import {TasksHistoryParams} from "./interfaces";


const DashboardEtlHistory: React.FC = () => {
    const api = useEtlApi();
    const [tasks, setTasks] = useState<TasksHistoryParams[]>([]);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);

    /* Fetch tasks history */
    const fetchHistory = async () => {
        setIsRefreshing(true);
        try {
            const response = await api("/tasks/", {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            });
            const formatted = response.map((task: TasksHistoryParams) => ({
                ...task,
                created_at: new Date(task.created_at),
                started_at: new Date(task.started_at),
                ended_at: task.ended_at ? new Date(task.ended_at) : null,
            }));

            setTasks(formatted);
            setLastUpdate(new Date());
        } catch (error) {
            toast.error("Error fetching history, try again later");
        } finally {
            setTimeout(() => setIsRefreshing(false), 500);
        }
    };

    useEffect(() => {
        // Fetch initial data
        fetchHistory();

        // Set up interval to refresh every 10 seconds
        const intervalId = setInterval(() => {
            fetchHistory();
        }, 10000);

        // Cleanup: clear interval when component unmounts
        return () => clearInterval(intervalId);
    }, []);

    const formatLastUpdate = () => {
        if (!lastUpdate) return "Never";
        return lastUpdate.toLocaleString("fr-FR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    };


    return (
        <>
            <div className="mb-4">
                <Breadcrumbs />
            </div>
            <h1 className="text-2xl font-semibold mr-4">ETL History</h1>

            <div className="flex items-center mb-4 gap-2">
                <p className="text-base-content/70">Watch tasks history</p>
                <AlertApiKey />
                <div className="ml-auto flex items-center gap-2">
                    <span className="text-sm text-base-content/60">
                        Last update: {formatLastUpdate()}
                    </span>
                    <button
                        className="btn btn-sm btn-circle btn-ghost"
                        onClick={fetchHistory}
                        disabled={isRefreshing}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={1.5}
                            stroke="currentColor"
                            className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`}
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
                            />
                        </svg>
                    </button>
                </div>
            </div>

            <div className="flex flex-col space-y-2">
                <TasksHistory tasks={tasks} fetch={fetchHistory} />
            </div>
        </>
    );
};

export default DashboardEtlHistory;