import axios from 'axios';
import logger from '../utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    logger.logApiRequest(
      config.method?.toUpperCase() || 'GET',
      config.url || '',
      config.data
    );
    return config;
  },
  (error) => {
    logger.error('API request error', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    logger.logApiResponse(
      response.config.method?.toUpperCase() || 'GET',
      response.config.url || '',
      response.status,
      response.data
    );
    return response;
  },
  (error) => {
    const method = error.config?.method?.toUpperCase() || 'GET';
    const url = error.config?.url || '';
    const status = error.response?.status || 0;
    
    logger.logApiResponse(method, url, status, error.response?.data);
    
    if (error.response?.data?.detail) {
      const detailError = new Error(error.response.data.detail);
      logger.error('API error with detail', detailError, {
        status,
        url,
        response: error.response.data
      });
      throw detailError;
    }
    
    logger.error('API error', error, {
      status,
      url,
      response: error.response?.data
    });
    
    throw error;
  }
);