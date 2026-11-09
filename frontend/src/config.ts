export type AppConfig = {
  apiBaseUrl: string;
};

const defaultApiBaseUrl = import.meta.env.DEV ? "/api/v1" : "http://localhost:8000/api/v1";

export const appConfig: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl
};
