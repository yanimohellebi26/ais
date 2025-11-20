import React from "react";
import { Pipeline } from "../interfaces";

interface Props {
    pipeline: Pipeline;
}

const PipelineDetails: React.FC<Props> = ({ pipeline }) => (
    <div className="alert alert-outline flex-1/2 flex flex-col items-start">
    <span>
      Steps - <strong>{pipeline.steps.length}</strong>
    </span>
        <span>{pipeline.description}</span>
    </div>
);

export default PipelineDetails;
