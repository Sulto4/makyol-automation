import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Inject Bearer token from the auth store on every request.
 */
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

/**
 * Response error interceptor:
 * - Normalizes error messages
 * - On 401: clear the session so ProtectedRoute bounces to /login
 *   (skip when the 401 came from /auth/login or /auth/register — those are expected)
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const status = error.response.status;
      const requestUrl = (error.config?.url ?? '').toString();
      const isAuthFlow = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register');

      if (status === 401 && !isAuthFlow) {
        const { logout, token } = useAuthStore.getState();
        if (token) logout();
      }

      const data = error.response.data as any;
      const errorObj = data?.error;
      const message =
        typeof errorObj === 'string'
          ? errorObj
          : errorObj?.message ?? 'A apărut o eroare neașteptată';
      return Promise.reject(new Error(message));
    }
    return Promise.reject(new Error('Eroare de conexiune la server'));
  },
);

export default apiClient;
