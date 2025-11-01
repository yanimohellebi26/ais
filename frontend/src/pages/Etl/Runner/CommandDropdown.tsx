import { FileTerminal, Play } from "lucide-react";
import React, { useState, useEffect } from "react";
import { useEtlApi } from "../../../hooks/useEtlApi";
import { toast } from "react-toastify";
import { useEtlWebSocket } from "../../../hooks/useEtlWebsocket";
import {Command} from "./interfaces";

interface Props {
    command: Command;
    index: number;
}

const CommandDropdown: React.FC<Props> = ({ command, index }) => {
    const api = useEtlApi();
    const [taskId, setTaskId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);

    const [paramValues, setParamValues] = useState<Record<string, any>>(() =>
        command.params.reduce((acc, param) => {
            acc[param.name] = param.default === "Sentinel.UNSET" ? "" : param.default;
            return acc;
        }, {} as Record<string, any>)
    );

    const handleChange = (name: string, value: any) => {
        setParamValues((prev) => ({ ...prev, [name]: value }));
    };

    const handleExecute = async () => {
        try {
            setIsLoading(true);
            const body: Record<string, any> = {};
            command.params.forEach((param) => {
                let value = paramValues[param.name];
                if (param.type === "integer") value = parseInt(value, 10);
                else if (param.type === "float") value = parseFloat(value);
                body[param.name] = value;
            });

            const result = await api(`/commands/${command.name}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            if (result?.task_id) {
                toast.success("Command queued!");
                setTaskId(result.task_id);
                setLogs([`[${new Date().toLocaleTimeString()}] Task started...`]);
            } else {
                toast.warning("Command executed but no task_id returned.");
                setIsLoading(false);
            }
        } catch (err: any) {
            console.error(err);
            setIsLoading(false);
            toast.error(`Failed to execute command: ${err.message}`);
        }
    };

    // Websocket
    const { messages } = useEtlWebSocket(taskId ? `/tasks/${taskId}` : null);
    const lastIndexRef = React.useRef(0);

    useEffect(() => {
        if (messages.length === 0) return;

        const newMessages = messages.slice(lastIndexRef.current);

        newMessages.forEach((msg) => {
            if (msg.type === "logs") {
                msg.data.forEach((log: any) => {
                    const status = log.status;
                    const payload = typeof log.payload === "string" ? log.payload : JSON.stringify(log.payload);
                    const formattedMsg = `[${new Date().toLocaleTimeString()}] ${status}: ${payload}`;
                    setLogs((prev) => [...prev, formattedMsg]);
                });
            }

            else if (msg.type === "end") {
                const formattedMsg = `[${new Date().toLocaleTimeString()}] Task ${msg.data}`;
                setLogs((prev) => [...prev, formattedMsg]);
                setIsLoading(false);
                setTaskId(null);
            }
        });

        lastIndexRef.current = messages.length;
    }, [messages]);


    return (
        <div
            key={index}
            tabIndex={0}
            className="collapse collapse-arrow bg-base-100 border-base-300 border"
        >
            <div className="collapse-title font-semi-bold">
                <div className="flex gap-2 items-center">
                    <FileTerminal />
                    <span className="font-semibold capitalize">{command.name}</span>
                    <span className="text-base-content/70">{command.help}</span>
                </div>
            </div>

            <div className="collapse-content text-sm flex flex-col gap-2">
                <div className="flex items-end gap-4 flex-wrap">
                    {command.params.length > 0 ? (
                        command.params.map((param, i) => (
                            <div key={i} className="form-control">
                                <label className="label">
                                    <span className="label-text font-medium">
                                        {param.name}
                                        {param.required && <span className="text-error ml-1">*</span>}
                                    </span>
                                    <span className="label-text-alt text-xs text-base-content/70">
                                        {param.help}
                                    </span>
                                </label>
                                <input
                                    type={param.type === "integer" ? "number" : "text"}
                                    value={paramValues[param.name]}
                                    onChange={(e) => handleChange(param.name, e.target.value)}
                                    className="input input-bordered w-full"
                                />
                            </div>
                        ))
                    ) : (
                        <p className="text-base-content/60">No parameters for this command.</p>
                    )}

                    <button
                        className="btn btn-primary mt-2 flex items-center gap-2"
                        onClick={handleExecute}
                        disabled={isLoading}
                    >
                        <Play /> Execute
                        {isLoading && <span className="loading loading-spinner loading-sm" />}
                    </button>
                </div>

                {/* Real-time message*/}
                {logs.length > 0 && (
                    <div className="bg-base-200 rounded-lg p-2 mt-3 text-xs font-mono max-h-48 overflow-y-auto">
                        {logs.map((msg, i) => (
                            <div key={i} className="whitespace-pre-wrap">
                                {msg}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CommandDropdown;
