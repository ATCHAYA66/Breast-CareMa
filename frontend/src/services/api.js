import axios from 'axios';

// Axios instance with base URL (proxied via Vite to http://localhost:8000)
const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

export const patientsApi = {
  createOrUpdate: (patientData) => api.post('/patients', patientData),
  getById: (patientId) => api.get(`/patients/${patientId}`),
  update: (patientId, data) => api.put(`/patients/${patientId}`, data),
};

export const diagnosisApi = {
  create: (modality, patientId = null) => api.post('/diagnosis/create', { modality, patient_id: patientId }),
  uploadImage: (studyId, imageType, file) => {
    const formData = new FormData();
    formData.append('study_id', studyId);
    formData.append('image_type', imageType);
    formData.append('file', file);
    return api.post('/diagnosis/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  analyze: (studyId, patientId = null) => {
    const formData = new FormData();
    formData.append('study_id', studyId);
    if (patientId) {
      formData.append('patient_id', patientId);
    }
    return api.post('/diagnosis/analyze', formData);
  },
  getById: (studyId) => api.get(`/diagnosis/${studyId}`),
  getHistory: () => api.get('/diagnosis/history'),
};

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
};

export const modelsApi = {
  getStatus: () => api.get('/models/status'),
  getMetrics: () => api.get('/models/metrics'),
};

export const reportsApi = {
  getReportMetadata: (studyId) => api.get(`/reports/${studyId}`),
  getPdfUrl: (studyId) => `/api/reports/${studyId}/pdf`,
};

export const researchApi = {
  getStatus: () => api.get('/research/busi/status'),
  analyze: (file, studyId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (studyId) {
      formData.append('study_id', studyId);
    }
    return api.post('/research/busi/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default api;
