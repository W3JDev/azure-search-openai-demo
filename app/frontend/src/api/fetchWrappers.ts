const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request<T>(path: string, options: RequestInit, token?: string): Promise<T> {
    const headers = new Headers(options.headers);
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }
    if (response.status === 204) {
        return undefined as T;
    }
    return (await response.json()) as T;
}

export async function getJson<T>(path: string, token?: string): Promise<T> {
    return request<T>(path, { method: "GET" }, token);
}

export async function postJson<T, B>(path: string, body: B, token?: string): Promise<T> {
    return request<T>(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    }, token);
}

export async function postForm<T>(path: string, form: FormData, token?: string): Promise<T> {
    return request<T>(path, { method: "POST", body: form }, token);
}

export async function del<T>(path: string, token?: string): Promise<T> {
    return request<T>(path, { method: "DELETE" }, token);
}
