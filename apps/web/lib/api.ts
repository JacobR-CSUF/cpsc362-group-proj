import axios from 'axios';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://api.geeb.pp.ua';

type ApiResponse<T> = {
  success: boolean;
  data: T;
  message?: string;
};

const isBrowser = typeof window !== 'undefined';

// Create axios instance
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    if (isBrowser) {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle 401 errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401 && isBrowser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    
    if (isBrowser) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<{ message: string; user: User }> => {
    const response = await api.post<{ message: string; user: User }>('/auth/register', data);
    return response.data;
  },

  logout: () => {
    if (isBrowser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<ApiResponse<User>>('/api/v1/users/me');
    return response.data.data;
  },
};

// Users API calls
export const usersAPI = {
  getProfile: async (userId: string): Promise<User> => {
    const response = await api.get<ApiResponse<User>>(`/api/v1/users/${userId}`);
    return response.data.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await api.put<ApiResponse<User>>('/api/v1/users/me', data);
    return response.data.data;
  },
};

export default api;
