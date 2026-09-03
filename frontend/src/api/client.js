import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    ...(import.meta.env.VITE_API_KEY && {
      Authorization: `Bearer ${import.meta.env.VITE_API_KEY}`,
    }),
  },
});

export default apiClient;
