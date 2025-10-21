import axios, { AxiosError } from 'axios';

// --- API CONFIGURATION ---
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- JWT TOKEN INTERCEPTOR ---
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- TYPESCRIPT INTERFACES ---

// Auth
export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  role: string;
}

// Dashboard
export interface Dashboard {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  owner_id: number;
}

// Metric
export interface Metric {
  id: number;
  name: string;
  value: number;
  metric_type: 'gauge' | 'counter' | 'histogram';
  dashboard_id: number;
  created_at: string;
}

export interface MetricIngest {
  dashboard_id: number;
  name: string;
  value: number;
  metric_type?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface IngestResponse {
  message: string;
}

// Error
export interface ApiError {
  detail: string | { msg: string; type: string; loc: (string | number)[] }[];
}

// --- API METHODS ---

/**
 * Handles API errors in a consistent way.
 * @param error The error object from Axios.
 * @returns A rejected promise with a formatted error message.
 */
const handleError = (error: AxiosError<ApiError>) => {
  if (error.response) {
    console.error('API Error:', error.response.data);
    const errorData = error.response.data;
    let errorMessage = 'An unknown error occurred.';

    if (typeof errorData.detail === 'string') {
      errorMessage = errorData.detail;
    } else if (Array.isArray(errorData.detail)) {
      errorMessage = errorData.detail.map(d => d.msg).join(', ');
    }

    return Promise.reject(errorMessage);
  } else if (error.request) {
    console.error('Network Error:', error.request);
    return Promise.reject('Network error. Please check your connection.');
  } else {
    console.error('Error:', error.message);
    return Promise.reject(error.message);
  }
};

// --- AUTH API ---

export const register = async (email: string, password: string): Promise<User> => {
  try {
    const response = await api.post<User>('/auth/register', { email, password });
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post<AuthResponse>('/auth/login/access-token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

// --- DASHBOARD API ---

export const getDashboards = async (): Promise<Dashboard[]> => {
  try {
    const response = await api.get<Dashboard[]>('/dashboards');
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

export const createDashboard = async (name: string, description: string): Promise<Dashboard> => {
  try {
    const response = await api.post<Dashboard>('/dashboards', { name, description });
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

export const getDashboard = async (id: number): Promise<Dashboard> => {
  try {
    const response = await api.get<Dashboard>(`/dashboards/${id}`);
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

export const getDashboardMetrics = async (dashboardId: number): Promise<Metric[]> => {
  try {
    const response = await api.get<Metric[]>(`/dashboards/${dashboardId}/metrics`);
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

// --- METRICS API ---

export const ingestMetrics = async (metrics: MetricIngest[]): Promise<IngestResponse> => {
  try {
    const response = await api.post<IngestResponse>('/metrics/ingest', metrics);
    return response.data;
  } catch (error) {
    return handleError(error as AxiosError<ApiError>);
  }
};

export default api;
