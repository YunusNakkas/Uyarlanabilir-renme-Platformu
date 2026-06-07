// Author: Fatma Türkmen - API Kimlik Doğrulama ve Kullanıcı İstek Katmanı
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
});

// Token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/giris';
    }
    return Promise.reject(err);
  }
);

/* ─── Auth Endpoints ─── */
export const authApi = {
  /** Kullanıcı kaydı */
  register: (data) => api.post('/auth/register', data),

  /** Giriş */
  login: (email, password) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  /** Şifre sıfırlama isteği */
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),

  /** Şifre güncelle */
  resetPassword: (token, newPassword) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }),
};

/* ─── User / Profile Endpoints ─── */
export const userApi = {
  /** Profil bilgilerini getir */
  getProfile: () => api.get('/users/me'),

  /** Profil güncelle */
  updateProfile: (data) => api.put('/users/me', data),

  /** Şifre değiştir */
  changePassword: (currentPassword, newPassword) =>
    api.put('/users/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  /** Avatar yükle */
  uploadAvatar: (file) => {
    const form = new FormData();
    form.append('avatar', file);
    return api.post('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /** Hesabı sil */
  deleteAccount: () => api.delete('/users/me'),
};

export default api;
