import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  login: (email, password) => 
    api.post('/api/auth/login', { email, password }),
  
  register: (email, password) => 
    api.post('/api/auth/register', { email, password }),
};

// Foods API
export const foodsAPI = {
  getFoods: (search = '') => 
    api.get(`/api/foods?search=${search}`),
  
  addFood: (foodData) => 
    api.post('/api/foods', foodData),
  
  estimateFood: (name) => 
    api.post('/api/foods/estimate', { name }),
};

// Meals API
export const mealsAPI = {
  logMeal: (items, date = null) => 
    api.post('/api/meals', { items, date }),
};

// Nutrition API
export const nutritionAPI = {
  getSummary: (date = null) => 
    api.get(`/api/summary${date ? `?date=${date}` : ''}`),
  
  getGoals: () => 
    api.get('/api/goals'),
  
  setGoals: (goals) => 
    api.post('/api/goals', goals),
};

// Chat API
export const chatAPI = {
  sendMessage: (message, history = []) => 
    api.post('/api/chat', { message, history }),
};

export default api;
