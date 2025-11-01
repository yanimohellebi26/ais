import React, { useEffect, useState } from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import AlertApiKey from "../AlertApiKey";
import { useEtlApi } from "../../../hooks/useEtlApi";
import { useLoading } from "../../../context/LoadingContext";
import { toast } from "react-toastify";
import { Pipeline } from "./interfaces";
import PipelineSelector from "./PipelineSelector";
import PipelineSteps from "./PipelineSteps";
import {useEtlWebSocket} from "../../../hooks/useEtlWebsocket";
import PipelineMessages from "./PipelineMessages";

const DashboardEtlPipelines: React.FC = () => {
    const api = useEtlApi();
    const { setLoading } = useLoading();
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
    const [pipelineStatus, setPipelineStatus] = useState<{index:number, status:string }>({index:0, status:""});
    const [running, setRunning] = useState(false);
    const [taskId, setTaskId] = useState<string | null>(null);

    /* Fetch all pipelines available */
    useEffect(() => {
        const fetchPipelines = async () => {
            setLoading(true);
            try {
                const response = await api("/pipelines/", {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                });
                setPipelines(response.pipelines);
            } catch (error) {
                toast.error("Error fetching pipelines, try again later");
            } finally {
                setLoading(false);
            }
        };
        fetchPipelines();
    }, []);

    /* Start pipeline with api call */
    const handleStartPipeline = async ({pipeline, selectedFile, continueOnError, useTimer}: {
        pipeline: Pipeline;
        selectedFile: string | null;
        continueOnError: boolean;
        useTimer: boolean;
    }) => {
        setLoading(true);
        try {
            const response = await api(`/pipelines/${pipeline.pipeline_name}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    file: selectedFile,
                    continue_on_error: continueOnError,
                    use_timer: useTimer,
                }),
            });
            setTaskId(response.task_id);
            setPipelineStatus({index:0, status:""});
            toast.success("Pipeline started successfully");
            setRunning(true);
        } catch (error) {
            toast.error("Failed to start pipeline");
        } finally {
            setLoading(false);
        }
    };

    const handleRevokePipeline = async () => {
        if(!taskId) return;
        try {
            const response = await api(`/tasks/${taskId}/revoke`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });
            toast.success("Pipeline revoked successfully");
        } catch (error) {
            toast.error("Failed to revoke pipeline");
        }
    }

    /* Open websocket for real-time messages */

    const { messages } = useEtlWebSocket(taskId ? `/tasks/${taskId}` : null);
    const lastIndexRef = React.useRef(0);

    useEffect(() => {
        if (messages.length === 0) return;

        const newMessages = messages.slice(lastIndexRef.current);

        newMessages.forEach((msg) => {
            if (msg.type === "logs") {
                msg.data.forEach((log: any) => {
                    if (log.type === "step") {
                        setPipelineStatus({"index":log.payload.index,"status":log.status});
                    }
                });
            }

            if (msg.type === "end") {
                setPipelineStatus((prevState)=> {
                    return {"index":prevState.index,"status":msg.data};
                });
                toast.success(`Pipeline ended with status ${msg.data}`);
                setTaskId(null)
                setRunning(false);
            }
        });

        lastIndexRef.current = messages.length;

    }, [messages]);


    return (
        <>
            <div className="mb-4">
                <Breadcrumbs />
            </div>

            <h1 className="text-2xl font-semibold mr-4">ETL Pipelines</h1>

            <div className="flex items-center mb-4 gap-2">
                <p className="text-base-content/70">Run pipelines and watch execution</p>
                <AlertApiKey />
            </div>

            <div className="flex flex-col space-y-8">
                <PipelineSelector
                    pipelines={pipelines}
                    selectedPipeline={selectedPipeline}
                    setSelectedPipeline={setSelectedPipeline}
                    setPipelineStatus={setPipelineStatus}
                    running={running}
                    onStart={handleStartPipeline}
                    onStop={handleRevokePipeline}
                />
                <div className="flex gap-4">
                    <PipelineSteps className="flex-1" pipeline={selectedPipeline} status={pipelineStatus} />
                    <PipelineMessages className="flex-1/2" logs={messages}  />
                </div>
            </div>
        </>
    );
};

export default DashboardEtlPipelines;
