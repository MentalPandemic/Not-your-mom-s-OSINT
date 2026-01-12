import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { toast } from 'react-hot-toast';

// API Configuration
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const API_TIMEOUT = parseInt(process.env.VITE_API_TIMEOUT || '30000');
const RETRY_ATTEMPTS = parseInt(process.env.VITE_API_RETRY_ATTEMPTS || '3');
const RETRY_DELAY = parseInt(process.env.VITE_API_RETRY_DELAY || '1000');

interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

interface RetryConfig {
  attempts: number;
  delay: number;
  shouldRetry?: (error: AxiosError) => boolean;
}

class ApiClient {
  private instance: AxiosInstance;
  private requestQueue: Map<string, Promise<any>> = new Map();

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for deduplication
        const requestId = this.generateRequestId(config);
        config.headers['X-Request-ID'] = requestId;

        // Add timestamp
        config.headers['X-Timestamp'] = Date.now().toString();

        // Log request in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => {
        // Log response in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`API Response: ${response.status} ${response.config.url}`, response.data);
        }

        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Handle retry logic
        if (this.shouldRetry(error) && !originalRequest._retry) {
          originalRequest._retry = true;
          await this.delay(RETRY_DELAY);
          return this.instance(originalRequest);
        }

        // Handle specific error cases
        if (error.response?.status === 401) {
          // Unauthorized - redirect to login or refresh token
          this.handleUnauthorized();
        } else if (error.response?.status === 403) {
          // Forbidden
          toast.error('You do not have permission to perform this action');
        } else if (error.response?.status === 429) {
          // Rate limited
          toast.error('Too many requests. Please wait before trying again.');
        } else if (error.response?.status >= 500) {
          // Server error
          toast.error('Server error occurred. Please try again later.');
        }

        // Transform error
        const apiError: ApiError = {
          message: this.getErrorMessage(error),
          code: error.code,
          status: error.response?.status,
          details: error.response?.data,
        };

        return Promise.reject(apiError);
      }
    );
  }

  private getAuthToken(): string | null {
    // Get token from localStorage, sessionStorage, or Redux store
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  private generateRequestId(config: AxiosRequestConfig): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private shouldRetry(error: AxiosError): boolean {
    // Don't retry on 4xx errors except 408 (timeout) and 429 (rate limit)
    if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
      return error.response.status === 408 || error.response.status === 429;
    }

    // Retry on network errors, timeouts, and 5xx errors
    return !error.response || error.response.status >= 500 || error.code === 'ECONNABORTED';
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private getErrorMessage(error: AxiosError): string {
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    
    if (error.response?.data?.error) {
      return error.response.data.error;
    }
    
    if (error.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred';
  }

  private handleUnauthorized() {
    // Clear tokens
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
    
    // Redirect to login or trigger auth refresh
    window.location.href = '/login';
  }

  // Generic HTTP methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.get(url, config);
    return response.data;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.post(url, data, config);
    return response.data;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.put(url, data, config);
    return response.data;
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.patch(url, data, config);
    return response.data;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.delete(url, config);
    return response.data;
  }

  // Request deduplication
  async deduplicateRequest<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    if (this.requestQueue.has(key)) {
      return this.requestQueue.get(key)!;
    }

    const promise = requestFn().finally(() => {
      this.requestQueue.delete(key);
    });

    this.requestQueue.set(key, promise);
    return promise;
  }

  // Upload progress tracking
  async uploadWithProgress<T = any>(
    url: string,
    formData: FormData,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    
    return response.data;
  }

  // Download with progress
  async downloadWithProgress(
    url: string,
    fileName: string,
    onProgress?: (progress: number) => void
  ): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
      onDownloadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    // Create blob and download
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Set authentication token
  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  // Clear authentication
  clearAuth(): void {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // Get axios instance for custom usage
  getInstance(): AxiosInstance {
    return this.instance;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export types
export type { ApiError, RetryConfig };