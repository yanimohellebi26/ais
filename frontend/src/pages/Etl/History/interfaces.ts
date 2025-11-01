export interface TasksHistoryParams {
    task_id:string;
    command:string;
    pipeline?:string;
    file?:string;
    kwargs:object;
    user:string;
    status:string;
    created_at:Date;
    started_at:Date;
    ended_at:Date;
}