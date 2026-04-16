import axios from 'axios'
import { toastError } from '../stores/toastStore'
import { useAuthStore } from '../stores/authStore'

const DEVICE_ID_KEY = 'resumeforge_device_id'

function getOrCreateDeviceId(): string {
  let id = localStorage.getItem(DEVICE_ID_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(DEVICE_ID_KEY, id)
  }
  return id
}

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  config.headers['X-Device-ID'] = getOrCreateDeviceId()
  const token = useAuthStore.getState().token
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(error)
    }
    if (error.response?.status === 429) {
      toastError('操作过于频繁，请稍后再试')
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (email: string, password: string, name?: string) =>
    api.post('/auth/register', { email, password, name }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
}

export const activationApi = {
  activate: (code: string, deviceName?: string) =>
    api.post('/activation/activate', { code, device_id: getOrCreateDeviceId(), device_name: deviceName }),
  status: (deviceId: string) => api.get(`/activation/status/${deviceId}`),
}

export const materialsApi = {
  upload: (formData: FormData) =>
    api.post('/materials/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  createText: (data: { title: string; content: string }) =>
    api.post('/materials/text', data),
  list: (params?: { type?: string; parse_status?: string; page?: number; page_size?: number }) =>
    api.get('/materials', { params }),
  get: (id: string) => api.get(`/materials/${id}`),
  delete: (id: string) => api.delete(`/materials/${id}`),
}

export const jdsApi = {
  create: (data: { title: string; company: string; jd_text: string }) =>
    api.post('/jds', data),
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/jds', { params }),
  get: (id: string) => api.get(`/jds/${id}`),
  update: (id: string, data: { title?: string; company?: string; jd_text?: string }) =>
    api.put(`/jds/${id}`, data),
  delete: (id: string) => api.delete(`/jds/${id}`),
  parse: (id: string) => api.post(`/jds/${id}/parse`),
}

export const analyzeApi = {
  analyzeSingle: (materialId: string) =>
    api.post(`/materials/${materialId}/analyze`),
  batchAnalyze: (data: { material_ids: string[] }) =>
    api.post('/materials/batch-analyze', data),
  getStatus: (materialId: string) =>
    api.get(`/materials/${materialId}/analyze/status`),
  retry: (materialId: string) =>
    api.post(`/materials/${materialId}/analyze/retry`),
  getResult: (materialId: string) =>
    api.get(`/materials/${materialId}/analysis`),
}

export const resumesApi = {
  generateBase: () => api.post('/resumes/base/generate'),
  getBase: () => api.get('/resumes/base'),
  updateBase: (data: { content: string }) => api.put('/resumes/base', data),
  generateTargeted: (data: { jd_id: string }) => api.post('/resumes/targeted/generate', data),
  listTargeted: (params?: { jd_id?: string; page?: number; page_size?: number }) =>
    api.get('/resumes/targeted', { params }),
  getTargeted: (id: string) => api.get(`/resumes/targeted/${id}`),
  updateTargeted: (id: string, data: { content: string }) =>
    api.put(`/resumes/targeted/${id}`, data),
  deleteTargeted: (id: string) => api.delete(`/resumes/targeted/${id}`),
  exportTargeted: (id: string, format: 'pdf' | 'docx' | 'txt') =>
    api.get(`/resumes/targeted/${id}/export/${format}`, {
      responseType: 'blob',
    }),
}

export const reviewsApi = {
  create: (data: { resume_id: string; resume_type: 'base' | 'targeted' }) =>
    api.post('/reviews', data),
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/reviews', { params }),
  get: (id: string) => api.get(`/reviews/${id}`),
  getStatus: (id: string) => api.get(`/reviews/${id}/status`),
  regenerateResume: (id: string) => api.post(`/reviews/${id}/regenerate-resume`),
  delete: (id: string) => api.delete(`/reviews/${id}`),
}

export default api
