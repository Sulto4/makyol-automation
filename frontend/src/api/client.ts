import axios from 'axios';
import type { ApiErrorResponse } from '../types';

/**
 * Axios instance configured for the backend API.
 * Uses '/api' baseURL which Vite dev server proxies to localhost:3000.
 */
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Response error interceptor — normalizes error messages
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const data = error.response.data as any;
      const errorObj = data?.error;
      const message = typeof errorObj === 'string'
        ? errorObj
        : errorObj?.message ?? 'A apărut o eroare neașteptată';
      return Promise.reject(new Error(message));
    }
    return Promise.reject(new Error('Eroare de conexiune la server'));
  },
);

export default apiClient;
