import axios from 'axios'

export const apiUrl = import.meta.env.VITE_API_URL?.trim().replace(/\/+$/, '')

export const api = axios.create({
  baseURL: apiUrl,
  timeout: 60000,
})
