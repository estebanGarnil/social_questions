<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"

import AppHeader from "@/components/AppHeader.vue"

const route = useRoute()
const isPlaying = computed(() => route.name === "list-play")
</script>

<template>
  <div class="app-shell" :class="{ 'is-playing': isPlaying }">
    <AppHeader />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>
