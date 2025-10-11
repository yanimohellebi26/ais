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

export interface User {
    id: number;
    username: string;
    email: string;
    role: Role;
    createAt: string;
    lastUpdate: string;
}