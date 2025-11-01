import React, { useEffect, useState } from "react";
import { Pipeline } from "./interfaces";
import {Play, Square} from "lucide-react";
import { toast } from "react-toastify";
import { useEtlApi } from "../../../hooks/useEtlApi";
import Select from "../../../components/BaseComponents/Select";

interface Props {
    pipelines: Pipeline[];
    selectedPipeline: Pipeline | null;
    setSelectedPipeline: (pipeline: Pipeline | null) => void;
    setPipelineStatus: (any:any) => void;
    running: boolean;
    onStart: (params: {
        pipeline: Pipeline;
        selectedFile: string | null;
        continueOnError: boolean;
        useTimer: boolean;
    }) => void;
    onStop: () => void;
}

const PipelineSelector: React.FC<Props> = ({
    pipelines,
    selectedPipeline,
    setSelectedPipeline,
    setPipelineStatus,
    running,
    onStart,
    onStop,
    }) => {
    const api = useEtlApi();
    const [files, setFiles] = useState<string[]>([]);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [continueOnError, setContinueOnError] = useState(false);
    const [useTimer, setUseTimer] = useState(true);

    useEffect(() => {
        const fetchFiles = async () => {
            try {
                const response = await api("/files/", {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                });
                setFiles(response);
            } catch (error) {
                toast.error("Error fetching available files, try again later");
            }
        };
        fetchFiles();
    },[]);

    return (
        <div className="rounded-2xl shadow-sm bg-base-100 p-4 border-accent space-y-2">
            <div className="flex flex-col gap-4">
                {/* Pipeline Selection */}
                <div className="flex gap-4">
                    <div className="flex-1/2">
                        <div className="flex flex-col justify-center">
                            <h1 className="text-xl font-semibold mr-4">Select Pipeline</h1>
                            <p className="text-base-content/70 mb-4">Choose a pipeline to execute</p>
                        </div>
                        <div className="flex items-end gap-4 flex-wrap">
                            <Select
                                value={selectedPipeline?.pipeline_name || "Select Pipeline"}
                                onChange={(val) => {
                                    const pipeline = pipelines.find((p) => p.pipeline_name === val) || null;
                                    setPipelineStatus({index:0, status:""});
                                    setSelectedPipeline(pipeline);
                                }}
                                options={[
                                    { label: "Select pipeline", value: "Select Pipeline", disabled: true },
                                    ...pipelines.map((p) => ({
                                        label: p.pipeline_name,
                                        value: p.pipeline_name,
                                    })),
                                ]}
                            />

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
                                    onClick={() => {
                                        if (selectedPipeline) {
                                            onStart({ pipeline: selectedPipeline, selectedFile, continueOnError, useTimer });
                                        }
                                    }}
                                >
                                    <Play /> Execute
                                </button>
                            )}

                        </div>
                    </div>

                    {selectedPipeline && (
                        <div className="alert alert-outline flex-1/2 flex flex-col items-start">
                            <span>Steps - <strong>{selectedPipeline.steps.length}</strong></span>
                            <span>{selectedPipeline.description}</span>
                        </div>
                    )}
                </div>

                {/* File selection & options */}
                {selectedPipeline && (
                    <div className="flex gap-4 items-center">
                        {files.length > 0 && (
                            <Select
                                value={selectedFile || "File"}
                                onChange={setSelectedFile}
                                options={[
                                    { label: "File", value: "File", disabled: true },
                                    ...files.map((f) => ({ label: f, value: f })),
                                ]}
                            />
                        )}

                        <label className="label flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={continueOnError}
                                onChange={(e) => setContinueOnError(e.target.checked)}
                                className="checkbox"
                            />
                            Continue On Error
                        </label>

                        <label className="label flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={useTimer}
                                onChange={(e) => setUseTimer(e.target.checked)}
                                className="checkbox"
                            />
                            Use timer
                        </label>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PipelineSelector;

