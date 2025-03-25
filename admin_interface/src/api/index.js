import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: 'http://localhost:3001', // The CRUD service URL
});

// Jobs API
export const jobsAPI = {
  getAll: () => api.get('/jobs'),
  getById: (id) => api.get(`/jobs/${id}`),
  create: (data) => api.post('/jobs', data),
  update: (id, data) => api.put(`/jobs/${id}`, data),
  delete: (id) => api.delete(`/jobs/${id}`),
};

// Scrape Targets API
export const scrapeTargetsAPI = {
  getAll: () => api.get('/scrape-targets'),
  getById: (id) => api.get(`/scrape-targets/${id}`),
  create: (data) => api.post('/scrape-targets', data),
  update: (id, data) => api.put(`/scrape-targets/${id}`, data),
  delete: (id) => api.delete(`/scrape-targets/${id}`),
};

// Media Generation Options API
export const mediaGenOptionsAPI = {
  getAll: () => api.get('/media-gen-options'),
  getById: (id) => api.get(`/media-gen-options/${id}`),
  create: (data) => api.post('/media-gen-options', data),
  update: (id, data) => api.put(`/media-gen-options/${id}`, data),
  delete: (id) => api.delete(`/media-gen-options/${id}`),
  getCategoryOptions: (id) => api.get(`/media-gen-options/${id}/category-options`),
};

// Media Category Options API
export const mediaCategoryOptionsAPI = {
  getAll: () => api.get('/media-category-options'),
  getById: (id) => api.get(`/media-category-options/${id}`),
  create: (data) => api.post('/media-category-options', data),
  update: (id, data) => api.put(`/media-category-options/${id}`, data),
  delete: (id) => api.delete(`/media-category-options/${id}`),
};

// Media Assets API
export const mediaAssetsAPI = {
  getAll: () => api.get('/media-assets'),
  getById: (id) => api.get(`/media-assets/${id}`),
  create: (data) => api.post('/media-assets', data),
  update: (id, data) => api.put(`/media-assets/${id}`, data),
  delete: (id) => api.delete(`/media-assets/${id}`),
};

export default {
  jobsAPI,
  scrapeTargetsAPI,
  mediaGenOptionsAPI,
  mediaCategoryOptionsAPI,
  mediaAssetsAPI,
};