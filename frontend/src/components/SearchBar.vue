<script setup lang="ts">
import { ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

withDefaults(
  defineProps<{
    compact?: boolean
    placeholder?: string
  }>(),
  {
    compact: false,
    placeholder: "Rechercher une liste ou un joueur…",
  },
)

const route = useRoute()
const router = useRouter()
const query = ref(route.name === "search" ? String(route.query.q ?? "") : "")

watch(
  () => route.query.q,
  (value) => {
    if (route.name === "search") {
      query.value = String(value ?? "")
    }
  },
)

async function submit() {
  const normalized = query.value.trim()
  if (!normalized) return
  await router.push({
    name: "search",
    query: { q: normalized },
  })
}
</script>

<template>
  <form
    class="global-search"
    :class="{ 'global-search-compact': compact }"
    role="search"
    @submit.prevent="submit"
  >
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="m21 21-4.35-4.35m2.35-5.15a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z"
      />
    </svg>
    <input
      v-model="query"
      type="search"
      :placeholder="placeholder"
      aria-label="Rechercher des listes ou des utilisateurs"
    />
    <button type="submit" :aria-label="compact ? 'Rechercher' : undefined">
      <span v-if="!compact">Rechercher</span>
      <span v-else aria-hidden="true">↵</span>
    </button>
  </form>
</template>
