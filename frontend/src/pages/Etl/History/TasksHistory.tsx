import React, {useState} from "react";
import {TasksHistoryParams} from "./interfaces";

interface Props {
    tasks: TasksHistoryParams[];
}

const TasksHistory: React.FC<Props> = ({tasks}) => {

    const formatDate = (date?: Date) => {
        if(!date) return;
        return date.toLocaleString("fr-FR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatDuration(ms: number) {
        const totalSeconds = Math.floor(ms / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        return `${hours > 0 ? `${hours}h ` : ""}${minutes}m ${seconds}s`;
    }

    const STATUS_CLASS: Record<string, string> = {
        success: "badge-success",
        error: "badge-error",
        running: "badge-primary",
        queued: "badge-info",
        revoked: "badge-secondary",
    };

    return (
        <div className="rounded-2xl shadow-sm max-h-140 bg-base-100 p-4 border-accent space-y-2">
            <h1 className="text-xl font-semibold">Execution History</h1>
            <div className="flex justify-between">
                <p className="text-base-content/70">Recent ETL script executions and their status</p>
                <div className="badge badge-primary">
                    {tasks.length} Tasks
                </div>
            </div>
            <div className="overflow-y-auto max-h-100">
                <table className="table">
                    <thead>
                    <tr>
                        <th>Task Name</th>
                        <th>Status</th>
                        <th>Created At</th>
                        <th>Duration</th>
                        <th>User</th>
                        <th>File</th>
                    </tr>
                    </thead>
                    <tbody>
                    {tasks.length > 0 && (
                        tasks.map((task) => {
                            return <tr>
                                <td>{task.pipeline ?? task.command}</td>
                                <td>
                                    <div className={`badge badge-soft ${STATUS_CLASS[task.status] || ''}`}>
                                        {task.status}
                                    </div>
                                </td>
                                <td>{formatDate(task.created_at)}</td>
                                <td>{formatDuration(task.ended_at.getTime() - task.started_at.getTime())}</td>
                                <td>{task.user}</td>
                                <td>{task.file ?? ''}</td>
                            </tr>
                        })
                    )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TasksHistory;