import api from './axios';

export async function listRequirements(params = {}) {
  const response = await api.get('/requirements', { params });
  return response.data;
}

export async function getRequirement(id) {
  const response = await api.get(`/requirements/${id}`);
  return response.data;
}

export async function createRequirement(payload) {
  const response = await api.post('/requirements', payload);
  return response.data;
}

export async function updateRequirement(id, payload) {
  const response = await api.put(`/requirements/${id}`, payload);
  return response.data;
}

export async function generateRequirement(id) {
  const response = await api.post(`/requirements/${id}/generate`);
  return response.data;
}

export async function reviewAI(id) {
  const response = await api.post(`/requirements/${id}/review-ai`);
  return response.data;
}

export async function reviewHuman(id, payload) {
  const response = await api.post(`/requirements/${id}/review-human`, payload);
  return response.data;
}

export async function approveRequirement(id) {
  const response = await api.post(`/requirements/${id}/approve`);
  return response.data;
}

export async function rejectRequirement(id, feedback) {
  const response = await api.post(`/requirements/${id}/reject`, { feedback });
  return response.data;
}

export async function exportRequirement(id) {
  const response = await api.get(`/requirements/${id}/export`, { responseType: 'blob' });
  return response.data;
}

export async function exportRequirementDocx(id) {
  const response = await api.get(`/requirements/${id}/export-docx`, { responseType: 'blob' });
  return response.data;
}

export async function getHistory(id) {
  const response = await api.get(`/requirements/${id}/history`);
  return response.data;
}

export async function listProjects() {
  const response = await api.get('/projects');
  return response.data;
}
