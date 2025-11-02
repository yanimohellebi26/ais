import React from "react";
import {Pipeline} from "./interfaces";
import Step from "./Step";

interface Props {
    pipeline: Pipeline | null;
    status: {
        index:number;
        status:string;
    };
    className?: string;
}

const PipelineSteps: React.FC<Props> = ({pipeline, status,className}) => {
    if (!pipeline) return;
    return (
        <div className={`rounded-2xl shadow-sm bg-base-100 p-4 border-accent ${className}`}>
            <h2 className="text-lg font-bold">Pipeline Progress <span className="badge badge-primary badge-soft">{pipeline.pipeline_name}</span></h2>
            <p className="text-base-content/60 mb-4">Step-by-step execution status</p>
            <div className="flex flex-col">
                {pipeline.steps.map((step, idx) => (
                    <Step
                        key={idx}
                        label={step.function_name}
                        done={status.index > idx+1 || (status.index === idx+1 && status.status === "success") }
                        active={status.index === idx+1}
                        error={status.index === idx + 1 && ["revoked", "error"].includes(status.status)}
                        isLast={idx === pipeline.steps.length - 1}
                    />
                ))}
            </div>
        </div>

    );
};

export default PipelineSteps;