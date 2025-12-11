export interface CommandParam {
    name: string;
    opts: string[];
    required: boolean;
    type: string;
    default: any;
    help: string;
    is_flag: boolean;
    nargs: number;

}

export interface Command {
    name: string;
    help: string;
    params: CommandParam[];
}

export interface Task {
    taskId: string;
    command: string;
    kwargs: Record<string, any>;
    user: string;
    status: string;
    createdAt: string;
    startedAt: string;
    endedAt: string;
    result: string;
    error: string | null;
}