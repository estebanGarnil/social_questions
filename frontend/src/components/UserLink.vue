<script setup lang="ts">
import { computed } from "vue"

import { useAuthStore } from "@/stores/auth"
import type { UserSummary } from "@/types"

const props = defineProps<{
  user: UserSummary
}>()

const auth = useAuthStore()
const destination = computed(() =>
  auth.user?.id === props.user.id
    ? { name: "profile" }
    : { name: "user-profile", params: { id: props.user.id } },
)
</script>

<template>
  <RouterLink class="user-link" :to="destination">
    <slot>{{ user.display_name }}</slot>
  </RouterLink>
</template>
