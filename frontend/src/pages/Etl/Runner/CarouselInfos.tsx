import React, { useEffect, useMemo, useState } from "react";
import { useEtlApi } from "../../../hooks/useEtlApi";
import { toast } from "react-toastify";
import {etlApiEmitter} from "../../../hooks/useEtlApiEmitter";
import StatCard from "./StatCard";
import {RefreshCcw} from "lucide-react";
import {Task} from "./interfaces";

const CarouselInfos: React.FC = () => {
    const api = useEtlApi();
    const [tasks, setTasks] = useState<Task[]>([]);
    const [rotate, setRotate] = useState(false);

    const fetchTasks = async () => {
        try {
            const data = await api("/tasks", {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            });
            const formattedTasks: Task[] = data.map((task: any) => ({
                taskId: task.task_id,
                command: task.command,
                kwargs: task.kwargs,
                user: task.user,
                status: task.status,
                createdAt: task.created_at,
                startedAt: task.started_at,
                endedAt: task.ended_at,
                result: task.result,
                error: task.error,
            }));
            setTasks(formattedTasks);
            setRotate(true);
            setTimeout(() => setRotate(false), 500);
        } catch (err: any) {
            toast.error("Failed to fetch ETL tasks");
        } finally {
        }
    };

    useEffect(() => {
        fetchTasks();

        const unsubscribe = etlApiEmitter.subscribe(() => {
            fetchTasks();
        });

        return () => unsubscribe();
    }, []);

    const tasksToday = useMemo(() => {
        const today = new Date();
        return tasks.filter((task) => {
            const created = new Date(task.createdAt);
            return (
                created.getFullYear() === today.getFullYear() &&
                created.getMonth() === today.getMonth() &&
                created.getDate() === today.getDate()
            );
        });
    }, [tasks]);

    const tasksTodayCount = tasksToday.length;
    const successTotal = tasks.filter(task => task.status === "success").length;
    const successToday = tasksToday.filter(task => task.status === "success").length;
    const failureTotal = tasks.filter(task => task.status === "error").length;
    const failureToday = tasksToday.filter(task => task.status === "error").length;
    const runningTotal = tasks.filter(task => task.status === "running").length;


    return (
        <>
            <div className="carousel rounded-box space-x-8">
                <div className="carousel-item rounded-box shadow-sm bg-base-100 p-2 flex justify-center items-center ">
                    <RefreshCcw
                        className={`cursor-pointer hover:scale-110 transition-transform duration-500 ${
                            rotate ? "rotate-[360deg]" : "rotate-0"
                        }`}
                        onClick={fetchTasks}
                    />
                </div>
                <div className="carousel-item rounded-box shadow-sm bg-base-100 p-6 w-50 flex justify-center">
                    <div className="flex items-center gap-2">
                        <h2 className="text-base-content/60">Running</h2>
                        <div className={`badge badge-soft badge-primary`}>{runningTotal}</div>
                    </div>
                </div>
                <StatCard
                    titleTotal="Total tasks"
                    titleToday="Tasks today"
                    totalValue={tasks.length}
                    todayValue={tasksTodayCount}
                    color="primary"
                />
                <StatCard
                    titleTotal="Success rate"
                    titleToday="Success rate today"
                    totalValue={`${((successTotal / tasks.length) * 100).toFixed(0)}%`}
                    todayValue={`${tasksTodayCount > 0 ? ((successToday / tasksTodayCount) * 100).toFixed(0) : "0"}%`}
                    color="success"
                />
                <StatCard
                    titleTotal="Failure rate"
                    titleToday="Failure rate today"
                    totalValue={`${((failureTotal / tasks.length) * 100).toFixed(0)}%`}
                    todayValue={`${tasksTodayCount > 0 ? ((failureToday / tasksTodayCount) * 100).toFixed(0) : "0"}%`}
                    color="error"
                />
            </div>
        </>

    );
};

export default CarouselInfos;
