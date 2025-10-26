import { FileTerminal, Play } from "lucide-react";
import React, { useState } from "react";
import { useEtlApi } from "../../../hooks/useEtlApi";
import { toast } from "react-toastify";


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

    const [paramValues, setParamValues] = useState<Record<string, any>>(
        () => command.params.reduce((acc, param) => {
            acc[param.name] = param.default === "Sentinel.UNSET" ? "" : param.default;
            return acc;
        }, {} as Record<string, any>)
    );

    const handleChange = (name: string, value: any) => {
        setParamValues(prev => ({ ...prev, [name]: value }));
    };

    const handleExecute = async () => {
        try {
            const body: Record<string, any> = {};
            command.params.forEach(param => {
                let value = paramValues[param.name];
                if (param.type === "integer") {
                    value = parseInt(value, 10);
                } else if (param.type === "float") {
                    value = parseFloat(value);
                }
                body[param.name] = value;
            });

            const result = await api(`/commands/${command.name}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            console.log(result);
            toast.success("Command added to queue!");
        } catch (err: any) {
            console.log(err);
            toast.error(`Failed to execute command : ${err.message}`);
        }
    };


    return (
        <div key={index} tabIndex={0} className="collapse collapse-arrow bg-base-100 border-base-300 border">
            <div className="collapse-title font-semi-bold">
                <div className="flex gap-2">
                    <FileTerminal />
                    <span className="font-semibold capitalize">{command.name}</span>
                    <span className="text-base-content/70">{command.help}</span>
                </div>
            </div>

            <div className="collapse-content text-sm flex items-end gap-2">
                {command.params.length > 0 ? (
                    command.params.map((param, i) => (
                        <div key={i} className="form-control">
                            <label className="label">
                                <span className="label-text font-medium">
                                    {param.name}
                                    {param.required && <span className="text-error ml-1">*</span>}
                                </span>
                                <span className="label-text-alt text-xs text-base-content/70">{param.help}</span>
                            </label>
                            <input
                                type={param.type === "integer" ? "number" : "text"}
                                value={paramValues[param.name]}
                                onChange={e => handleChange(param.name, e.target.value)}
                                className="input input-bordered w-full"
                            />
                        </div>
                    ))
                ) : (
                    <p className="text-base-content/60">No parameters for this command.</p>
                )}
                <button className="btn btn-primary mt-2" onClick={handleExecute}>
                    <Play /> Execute
                </button>
            </div>
        </div>
    );
};

export default CommandDropdown;
