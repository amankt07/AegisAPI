/**
 * AegisAPI Frontend API Service Layer
 * Centralized Axios client connecting to FastAPI security telemetry backend.
 * Provides normalized error handling, timeouts, and API functions.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Intercept responses for consistent error formatting
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMessage = 'An unexpected error occurred while communicating with the backend.';

    if (error.response) {
      // Backend returned HTTP status outside 2xx
      const data = error.response.data;
      if (data?.message) {
        errorMessage = data.message;
      } else if (data?.detail) {
        errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } else {
        errorMessage = `HTTP ${error.response.status}: ${error.response.statusText}`;
      }
    } else if (error.request) {
      // Request was made but no response received (backend offline)
      errorMessage = `Cannot connect to AegisAPI backend at ${API_BASE_URL}. Ensure the FastAPI server is running.`;
    } else {
      errorMessage = error.message;
    }

    return Promise.reject(new Error(errorMessage));
  }
);

/**
 * Check backend service health and active model loading state.
 * @returns {Promise<Object>}
 */
export const getHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Retrieve real-time dashboard telemetry KPIs and threat distribution.
 * @returns {Promise<Object>}
 */
export const getStatistics = async () => {
  const response = await apiClient.get('/statistics');
  return response.data;
};

/**
 * Retrieve chronological API traffic event history from SQLite.
 * @param {Object} params - { limit: number, offset: number }
 * @returns {Promise<Array>}
 */
export const getTraffic = async (params = {}) => {
  const { limit = 50, offset = 0 } = params;
  const response = await apiClient.get('/traffic', {
    params: { limit, offset },
  });
  return response.data;
};

/**
 * Retrieve detected security anomaly incidents from SQLite.
 * @param {Object} params - { limit: number, offset: number }
 * @returns {Promise<Array>}
 */
export const getAnomalies = async (params = {}) => {
  const { limit = 50, offset = 0 } = params;
  const response = await apiClient.get('/anomalies', {
    params: { limit, offset },
  });
  return response.data;
};

/**
 * Retrieve active machine learning model metadata, hyperparameters, and offline benchmarks.
 * @returns {Promise<Object>}
 */
export const getModelInfo = async () => {
  const response = await apiClient.get('/model-info');
  return response.data;
};

/**
 * Submit an incoming API traffic telemetry record for real-time anomaly scoring.
 * @param {Object} payload - API request telemetry object
 * @returns {Promise<Object>}
 */
export const predictTraffic = async (payload) => {
  const response = await apiClient.post('/predict', payload);
  return response.data;
};

/**
 * Submit a batch of API traffic telemetry records for vectorized evaluation.
 * @param {Array<Object>} records - Array of traffic records (max 500)
 * @returns {Promise<Object>}
 */
export const predictBatchTraffic = async (records) => {
  const response = await apiClient.post('/predict/batch', { records });
  return response.data;
};

export default apiClient;

