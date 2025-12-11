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
    userId: number;
    username: string;
    userEmail: string;
    userRole: string;
    vesselId: number;
    fileId: number;
    fileName: string;
    createdAt: string;
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
