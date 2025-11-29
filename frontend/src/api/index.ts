import axios, { AxiosResponse } from 'axios';
import {
  Report,
  CreateReportRequest,
  UpdateReportRequest,
  Finding,
  CreateFindingRequest,
  UpdateFindingRequest,
  RecommendedAction,
  CreateActionRequest,
  UpdateActionRequest,
  Comment,
  CreateCommentRequest,
  ReportStatusHistory,
  ApiResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';
const AGENT_API_URL = import.meta.env.VITE_AGENT_API_URL || 'http://localhost:8002';

// Create axios instance for main API
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create axios instance for agent service
const agentApiInstance = axios.create({
  baseURL: AGENT_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens (if needed later)
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('token');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

// Report API functions
export const reportApi = {
  // Get all reports
  getReports: async (params?: {
    skip?: number;
    limit?: number;
    cluster_id?: string;
    user_id?: string;
    enforce_access?: boolean;
  }): Promise<AxiosResponse<Report[]>> => {
    return api.get('/reports', { params });
  },

  // Get a specific report with full details
  getReport: async (reportId: string): Promise<AxiosResponse<Report>> => {
    return api.get(`/reports/${reportId}`);
  },

  // Create a new report
  createReport: async (reportData: CreateReportRequest): Promise<AxiosResponse<Report>> => {
    return api.post('/reports', reportData);
  },

  // Update a report
  updateReport: async (reportId: string, reportData: UpdateReportRequest): Promise<AxiosResponse<Report>> => {
    return api.put(`/reports/${reportId}`, reportData);
  },

  // Delete a report
  deleteReport: async (reportId: string): Promise<AxiosResponse<void>> => {
    return api.delete(`/reports/${reportId}`);
  },

  // Get similar reports
  getSimilarReports: async (reportId: string, limit?: number, user_id?: string): Promise<AxiosResponse<any>> => {
    return api.get(`/reports/${reportId}/similar`, { params: { limit, user_id } });
  },

  // Get findings for a report
  getFindings: async (reportId: string): Promise<AxiosResponse<Finding[]>> => {
    return api.get(`/reports/${reportId}/findings`);
  },

  // Create a finding for a report
  createFinding: async (reportId: string, findingData: CreateFindingRequest): Promise<AxiosResponse<Finding>> => {
    return api.post(`/reports/${reportId}/findings`, findingData);
  },

  // Update a finding
  updateFinding: async (findingId: string, findingData: UpdateFindingRequest): Promise<AxiosResponse<Finding>> => {
    return api.put(`/findings/${findingId}`, findingData);
  },

  // Delete a finding
  deleteFinding: async (findingId: string): Promise<AxiosResponse<void>> => {
    return api.delete(`/findings/${findingId}`);
  },

  // Get actions for a finding
  getActions: async (findingId: string): Promise<AxiosResponse<RecommendedAction[]>> => {
    return api.get(`/findings/${findingId}/actions`);
  },

  // Create an action for a finding
  createAction: async (findingId: string, actionData: CreateActionRequest): Promise<AxiosResponse<RecommendedAction>> => {
    return api.post(`/findings/${findingId}/actions`, actionData);
  },

  // Update an action
  updateAction: async (actionId: string, actionData: UpdateActionRequest): Promise<AxiosResponse<RecommendedAction>> => {
    return api.put(`/actions/${actionId}`, actionData);
  },

  // Get comments for a report
  getComments: async (reportId: string): Promise<AxiosResponse<Comment[]>> => {
    return api.get(`/reports/${reportId}/comments`);
  },

  // Create a comment for a report
  createComment: async (reportId: string, commentData: CreateCommentRequest): Promise<AxiosResponse<Comment>> => {
    return api.post(`/reports/${reportId}/comments`, commentData);
  },
};

// Health check
export const healthApi = {
  healthCheck: async (): Promise<AxiosResponse<{ status: string }>> => {
    return api.get('/health');
  },
};

// Agent API functions
export const agentApi = {
  // Generate AI-powered report
  generateReport: async (params: {
    database: string;
    app: string;
    prompt?: string;
  }): Promise<AxiosResponse<{
    success: boolean;
    error: string | null;
  }>> => {
    return agentApiInstance.post('/generate-report', params);
  },

  // Health check for agent service
  healthCheck: async (): Promise<AxiosResponse<{ status: string; service: string }>> => {
    return agentApiInstance.get('/health');
  },
};

export default api;
