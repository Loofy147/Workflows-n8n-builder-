import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

// Request interceptor for Auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error normalization and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Token refresh logic (placeholder for 2026)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // In real app: const response = await axios.post('/auth/refresh', { refresh_token });
        // localStorage.setItem('auth_token', response.data.access_token);
        // return api(originalRequest);
        console.warn('Authentication expired. Please log in again.');
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }

    // Error normalization
    const errorMessage =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      'Une erreur inattendue est survenue.';

    error.normalizedMessage = errorMessage;
    return Promise.reject(error);
  }
);

export const chatService = {
  sendMessage: async (message: string, conversationId?: string, userId: string = 'test-user') => {
    const response = await api.post('/chat/', {
      message,
      conversation_id: conversationId,
      user_id: userId,
    });
    return response.data;
  },
};

export const executionService = {
  getUserExecutions: async () => {
    const response = await api.get('/executions/');
    return response.data;
  },
};

export const workflowService = {
  getTemplates: async () => {
    const response = await api.get('/workflows/templates');
    return response.data;
  },
  activateWorkflow: async (templateId: string, inputs: any) => {
    const response = await api.post('/workflows/activate', {
      template_id: templateId,
      inputs: inputs,
    });
    return response.data;
  },
  getUserWorkflows: async () => {
    const response = await api.get('/workflows/');
    return response.data;
  },
};

export default api;
