export interface Role {
    id: number;
    name: string;
}

export interface UpdateUserRequest {
    id: number;
    username?: string;
    email?: string;
    password?: string;
    role?: string;
}

export interface UserAccount {
    id: number;
    username: string;
    email: string;
    role: string;
}

export interface User {
    id: number;
    username: string;
    email: string;
    role: Role;
    createAt: string;
    lastUpdate: string;
}

export interface ApiError extends Error {
    statusCode: number;
    message: string;
    path: string;
    timestamp: string;
}

export interface RequestPropertyAdmin {
    id: number;
    userid: number;
    username: string;
    user_email: string;
    user_role: string;
    mmsi: string;
    fileid: number;
    file_name: string;
    created_at: string;
}

export interface FileUploadDetails {
    id: number;
    user_id: number;
    original_filename: string;
    file_size: number;
    uploaded_at: string;
}

export interface PageResponse<T> {
    content: T[];
    totalElements: number;
    totalPages: number;
    number: number;
    size: number;
    first: boolean;
    last: boolean;
}
