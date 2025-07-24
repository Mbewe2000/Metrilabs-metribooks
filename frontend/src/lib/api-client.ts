import axios, { AxiosInstance, AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import { AuthTokens } from '@/types';

class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = Cookies.get('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newToken = await this.refreshToken();
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            this.logout();
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/login';
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    const refreshToken = Cookies.get('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/auth/token/refresh/`, {
      refresh: refreshToken,
    });

    const { access } = response.data;
    Cookies.set('access_token', access, { expires: 1 }); // 1 day
    
    return access;
  }

  public setTokens(tokens: AuthTokens) {
    Cookies.set('access_token', tokens.access, { expires: 1 }); // 1 day
    Cookies.set('refresh_token', tokens.refresh, { expires: 7 }); // 7 days
  }

  public logout() {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
  }

  public getTokens(): AuthTokens | null {
    const access = Cookies.get('access_token');
    const refresh = Cookies.get('refresh_token');
    
    if (access && refresh) {
      return { access, refresh };
    }
    
    return null;
  }

  // Generic HTTP methods
  public async get<T>(url: string, params?: Record<string, unknown>): Promise<AxiosResponse<T>> {
    return this.client.get(url, { params });
  }

  public async post<T>(url: string, data?: unknown): Promise<AxiosResponse<T>> {
    return this.client.post(url, data);
  }

  public async put<T>(url: string, data?: unknown): Promise<AxiosResponse<T>> {
    return this.client.put(url, data);
  }

  public async patch<T>(url: string, data?: unknown): Promise<AxiosResponse<T>> {
    return this.client.patch(url, data);
  }

  public async delete<T>(url: string): Promise<AxiosResponse<T>> {
    return this.client.delete(url);
  }
}

export const apiClient = new ApiClient();
