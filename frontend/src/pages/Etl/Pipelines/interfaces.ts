export interface FuncParameter {
    name: string;
    type: string;
    default: string | number | boolean | null;
}

export interface YamlKwargs {
    [key: string]: string[] | string | number | boolean | null;
}

export interface PipelineStep {
    function_name: string;
    description: string;
    parameters: FuncParameter[];
    yaml_kwargs: YamlKwargs;
}

export interface Pipeline {
    pipeline_name: string;
    steps: PipelineStep[];
    description: string;
}

export interface FileInfo {
    filename: string;
    size_bytes: number;
    columns: string[];
}