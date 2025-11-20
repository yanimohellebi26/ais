import React, { useEffect, useState } from "react";
import { Pipeline } from "../interfaces";
import { useEtlApi } from "../../../../hooks/useEtlApi";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import PipelineDropdown from "./PipelineDropdown";
import PipelineDetails from "./PipelineDetails";
import FileSelector from "./FileSelector";
import PipelineOptions from "./PipelineOptions";


interface Props {
    pipelines: Pipeline[];
    selectedPipeline: Pipeline | null;
    setSelectedPipeline: (pipeline: Pipeline | null) => void;
    setPipelineStatus: (any: any) => void;
    running: boolean;
    onStart: (params: {
        pipeline: Pipeline;
        selectedFiles: string[];
        continueOnError: boolean;
        useTimer: boolean;
        force: boolean;
    }) => Promise<boolean>;
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
    const navigate = useNavigate();

    const [files, setFiles] = useState<string[]>([]);
    const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
    const [continueOnError, setContinueOnError] = useState(false);
    const [useTimer, setUseTimer] = useState(true);
    const [force,setForce] = useState(false);

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
    }, []);

    return (
        <div className="rounded-2xl shadow-sm bg-base-100 p-4 border-accent space-y-4">
            <div className="flex flex-col gap-4">
                {/* Pipeline select */}
                <div className="flex gap-4">
                    <div className="flex-1/2">
                        <PipelineDropdown
                            pipelines={pipelines}
                            selectedPipeline={selectedPipeline}
                            running={running}
                            onStop={onStop}
                            onSelect={(p) => {
                                setPipelineStatus({ index: 0, status: "" });
                                setSelectedPipeline(p);
                            }}
                            onExecute={async () => {
                                if (selectedPipeline) {
                                    const shouldRedirect = await onStart({
                                        pipeline: selectedPipeline,
                                        selectedFiles,
                                        continueOnError,
                                        useTimer,
                                        force
                                    });
                                    if (shouldRedirect) navigate("/dashboard/etl/history");
                                }
                            }}
                        />
                    </div>

                    {selectedPipeline && (
                        <PipelineDetails pipeline={selectedPipeline} />
                    )}
                </div>

                {selectedPipeline && (
                    <>
                        <div className="flex flex-wrap items-baseline-last gap-6">
                            <div className="flex-1">
                                <FileSelector
                                    files={files}
                                    selectedFiles={selectedFiles}
                                    onToggleFile={(file) =>
                                        setSelectedFiles((prev) =>
                                            prev.includes(file)
                                                ? prev.filter((f) => f !== file)
                                                : [...prev, file]
                                        )
                                    }
                                    onRemoveFile={(file) =>
                                        setSelectedFiles((prev) => prev.filter((f) => f !== file))
                                    }
                                    hideSelectedList
                                />
                            </div>

                            <PipelineOptions
                                continueOnError={continueOnError}
                                useTimer={useTimer}
                                force={force}
                                onChangeContinue={setContinueOnError}
                                onChangeTimer={setUseTimer}
                                onChangeForce={setForce}
                            />
                        </div>

                        {selectedFiles.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-2">
                                {selectedFiles.map((file) => (
                                    <div key={file} className="badge badge-secondary badge-soft p-4 gap-2">
                                        {file}
                                        <button
                                            onClick={() =>
                                                setSelectedFiles((prev) => prev.filter((f) => f !== file))
                                            }
                                            className="btn btn-ghost btn-xs btn-secondary btn-circle"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}

            </div>
        </div>
    );
};

export default PipelineSelector;
