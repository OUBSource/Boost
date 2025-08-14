export type Headers = {[x: string]: string}

export interface ErrorResponse {
    message: string;
}


// App types
export interface Message {
    id: number;
    username: string;
    content: string;
    is_read: boolean;
    is_author: boolean;
    timestamp: string;
}

export interface Messages {
    messages: Message[];
}

export interface User {
    username: string;
}

export interface LoginResponse {
    username: string;
    token: string;
}