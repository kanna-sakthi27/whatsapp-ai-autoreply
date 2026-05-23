import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail 
      || error.response?.data?.error 
      || error.response?.data?.message
      || error.message
      || 'Unknown error'
    console.error('API Error:', message, error.response?.status)
    return Promise.reject(new Error(message))
  }
)

export default client
