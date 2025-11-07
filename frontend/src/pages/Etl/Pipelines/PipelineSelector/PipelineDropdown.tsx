import React from "react";
import { Pipeline } from "../interfaces";
import { Play, Square } from "lucide-react";

interface Props {
    pipelines: Pipeline[];
    selectedPipeline: Pipeline | null;
    running: boolean;
    onStop: () => void;
    onSelect: (pipeline: Pipeline | null) => void;
    onExecute: () => void;
}

const PipelineDropdown: React.FC<Props> = ({
                                               pipelines,
                                               selectedPipeline,
                                               running,
                                               onStop,
                                               onSelect,
                                               onExecute,
                                           }) => (
    <div>
        <div className="flex flex-col justify-center">
            <h1 className="text-xl font-semibold">Select Pipeline</h1>
            <p className="text-base-content/70 mb-4">Choose a pipeline to execute</p>
        </div>

        <div className="flex items-end gap-4 flex-wrap">
            <select
                className="select select-bordered"
                value={selectedPipeline?.pipeline_name || "Select Pipeline"}
                onChange={(e) => {
                    const selected =
                        pipelines.find((p) => p.pipeline_name === e.target.value) || null;
                    onSelect(selected);
                }}
            >
                <option value="Select Pipeline" disabled>
                    Select pipeline
                </option>
                {pipelines.map((p) => (
                    <option key={p.pipeline_name} value={p.pipeline_name}>
                        {p.pipeline_name}
                    </option>
                ))}
            </select>

            {running ? (
                <button
                    className="btn btn-error mt-2 flex items-center gap-2"
                    onClick={onStop}
                >
                    <Square /> Stop
                </button>
            ) : (
                <button
                    className="btn btn-primary mt-2 flex items-center gap-2"
                    onClick={onExecute}
                >
                    <Play /> Execute
                </button>
            )}
        </div>
    </div>
);

export default PipelineDropdown;
