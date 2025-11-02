import React, {useEffect, useState} from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import AlertApiKey from "../AlertApiKey";
import {useEtlApi} from "../../../hooks/useEtlApi";
import {useLoading} from "../../../context/LoadingContext";
import {toast} from "react-toastify";
import TasksHistory from "./TasksHistory";
import {TasksHistoryParams} from "./interfaces";


const DashboardEtlHistory: React.FC = () => {
    const api = useEtlApi();
    const { setLoading } = useLoading();
    const [tasks, setTasks] = useState<TasksHistoryParams[]>([]);

    /* Fetch tasks history */
    useEffect(() => {
        const fetchHistory = async () => {
            setLoading(true);
            try {
                const response = await api("/tasks/", {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                });
                const formatted = response.map((task: TasksHistoryParams) => ({
                    ...task,
                    created_at: new Date(task.created_at),
                    started_at: new Date(task.started_at),
                    ended_at: new Date(task.ended_at),
                }));

                setTasks(formatted);
            } catch (error) {
                toast.error("Error fetching history, try again later");
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);


    return (
        <>
            <div className="mb-4">
                <Breadcrumbs />
            </div>
            <h1 className="text-2xl font-semibold mr-4">ETL History</h1>

            <div className="flex items-center mb-4 gap-2">
                <p className="text-base-content/70">Watch tasks history</p>
                <AlertApiKey />
            </div>

            <div className="flex flex-col space-y-2">
                <TasksHistory tasks={tasks} />
            </div>
        </>
    );
};

export default DashboardEtlHistory;