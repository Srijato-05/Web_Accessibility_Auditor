import axios from 'axios';

// Fast API normally runs on 8000
export const client = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});
