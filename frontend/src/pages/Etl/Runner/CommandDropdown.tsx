import { FileTerminal, Play } from "lucide-react";
import React, { useState, useEffect } from "react";
import { useEtlApi } from "../../../hooks/useEtlApi";
import { toast } from "react-toastify";
import { useEtlWebSocket } from "../../../hooks/useEtlWebsocket";

interface CommandParam {
    name: string;
    opts: string[];
    required: boolean;
    type: string;
    default: any;
    help: string;
}

interface Command {
    name: string;
    help: string;
    params: CommandParam[];
}

interface CommandDropdownProps {
    command: Command;
    index: number;
}

const CommandDropdown: React.FC<CommandDropdownProps> = ({ command, index }) => {
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
                setIsLoading(true);
            } else {
                toast.warning("Command executed but no task_id returned.");
            }
        } catch (err: any) {
            console.error(err);
            toast.error(`Failed to execute command: ${err.message}`);
        }
    };

    // Websocket
    const { data } = useEtlWebSocket(taskId ? `/tasks/${taskId}` : null);

    useEffect(() => {
        if (!data) return;

        let msg = "";
        if (data.type === "log") {
            const { level, message } = data.data;
            msg = `[${new Date().toLocaleTimeString()}] (log) ${message}`;
        } else if (data.type === "meta") {
            msg = `[${new Date().toLocaleTimeString()}] (meta) status : ${data.data.status}`;
        } else if (data.type === "status") {
            msg = `[${new Date().toLocaleTimeString()}] (status) ${data.data}`;
        }

        setLogs((prev) => {
            if (prev.includes(msg)) return prev;
            return [...prev, msg];
        });

        if (data.type === "status" && ["success", "error", "revoked"].includes(data.data)) {
            setIsLoading(false);
            setTaskId(null);

            setLogs((prev) => {
                const finalMsg = `[${new Date().toLocaleTimeString()}] Task ${data.data}`;
                if (prev.includes(finalMsg)) return prev;
                return [...prev, finalMsg];
            });
        }
    }, [data]);


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
