<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="notice notice-error" role="alert">{{ message }}</div>
</template>
