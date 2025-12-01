import React from "react";
import { Pipeline } from "../interfaces";

interface Props {
    pipeline: Pipeline;
}

const PipelineDetails: React.FC<Props> = ({ pipeline }) => {
    const extractStep = pipeline.steps.find(
        step => step.function_name === "extract_data_from_file"
    );

    const requiredColumns = extractStep?.yaml_kwargs?.selected_map;

    return (
        <div className="alert alert-outline flex-1/2 flex flex-col items-start gap-2">
            <span>
                Steps - <strong>{pipeline.steps.length}</strong>
            </span>
            <span>{pipeline.description}</span>

            {requiredColumns && Array.isArray(requiredColumns) && requiredColumns.length > 0 && (
                <div className="mt-2 w-full">
                    <span className="font-semibold text-sm">Required columns:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                        {requiredColumns.map((col, index) => (
                            <span
                                key={index}
                                className="badge badge-sm badge-primary badge-outline"
                            >
                                {col}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default PipelineDetails;