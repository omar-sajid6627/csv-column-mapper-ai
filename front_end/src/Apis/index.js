import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const getCodeAndSuggestions = (formData) => api.post('/suggest_column_mapping/', formData);

export const updateSuggestions = (formData) => api.post('/suggest_column_mapping/', formData);

export const mapCode = (formData) => api.post('/column_mapper/', formData);

export const errorMessage = (error) => {
  const data = error?.response?.data;
  if (typeof data?.detail === 'string') {
    return data.line ? `Line ${data.line}: ${data.detail}` : data.detail;
  }
  return error?.response ? `Request failed (${error.response.status})` : 'Cannot reach the API';
};
