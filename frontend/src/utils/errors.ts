import axios from "axios"

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) {
    return fallback
  }

  const data = error.response?.data
  if (typeof data?.detail === "string") {
    return data.detail
  }
  if (data && typeof data === "object") {
    const firstValue = Object.values(data)[0]
    if (Array.isArray(firstValue) && typeof firstValue[0] === "string") {
      return firstValue[0]
    }
    if (typeof firstValue === "string") {
      return firstValue
    }
  }
  return fallback
}
