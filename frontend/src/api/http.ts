import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios"

const ACCESS_KEY = "questionly_access"
const REFRESH_KEY = "questionly_refresh"

export const api = axios.create({
  baseURL: "/api",
  timeout: 15_000,
})

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function storeTokens(access: string, refresh?: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh)
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

let refreshPromise: Promise<string> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryableRequest | undefined
    const refresh = getRefreshToken()

    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      !refresh ||
      original.url?.includes("/auth/token/refresh/")
    ) {
      return Promise.reject(error)
    }

    original._retry = true
    refreshPromise ??= axios
      .post("/api/auth/token/refresh/", { refresh })
      .then((response) => {
        const access = response.data.access as string
        const rotatedRefresh = response.data.refresh as string | undefined
        storeTokens(access, rotatedRefresh)
        return access
      })
      .catch((refreshError) => {
        clearTokens()
        window.dispatchEvent(new Event("auth-expired"))
        throw refreshError
      })
      .finally(() => {
        refreshPromise = null
      })

    const access = await refreshPromise
    original.headers.Authorization = `Bearer ${access}`
    return api(original)
  },
)
