import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

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
};

export default api;
