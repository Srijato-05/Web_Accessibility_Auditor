import axios from 'axios';

// Fast API normally runs on 8000. Use environment variable for deployed showcases.
export const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});
