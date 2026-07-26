import { defineStore } from "pinia"
import { computed, ref } from "vue"

import {
  api,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  storeTokens,
} from "@/api/http"
import type { UserProfile } from "@/types"

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserProfile | null>(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => Boolean(user.value))

  async function fetchMe(): Promise<void> {
    const response = await api.get<UserProfile>("/auth/me/")
    user.value = response.data
  }

  async function initialize(): Promise<void> {
    if (getAccessToken()) {
      try {
        await fetchMe()
      } catch {
        clearTokens()
      }
    }
    ready.value = true
  }

  async function login(email: string, password: string): Promise<void> {
    const response = await api.post<{ access: string; refresh: string }>(
      "/auth/token/",
      { email, password },
    )
    storeTokens(response.data.access, response.data.refresh)
    await fetchMe()
  }

  async function register(payload: {
    email: string
    display_name: string
    password: string
    password_confirm: string
  }): Promise<void> {
    await api.post("/auth/register/", payload)
    await login(payload.email, payload.password)
  }

  async function logout(): Promise<void> {
    const refresh = getRefreshToken()
    try {
      if (refresh) {
        await api.post("/auth/logout/", { refresh })
      }
    } finally {
      clearTokens()
      user.value = null
    }
  }

  window.addEventListener("auth-expired", () => {
    user.value = null
  })

  return {
    user,
    ready,
    isAuthenticated,
    initialize,
    login,
    register,
    logout,
    fetchMe,
  }
})
