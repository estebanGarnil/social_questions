<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import ListCard from "@/components/ListCard.vue"
import LoadingState from "@/components/LoadingState.vue"
import SearchBar from "@/components/SearchBar.vue"
import UserLink from "@/components/UserLink.vue"
import { useAuthStore } from "@/stores/auth"
import type { GlobalSearchResults, UserProfile } from "@/types"
import { apiErrorMessage } from "@/utils/errors"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const results = ref<GlobalSearchResults | null>(null)
const loading = ref(false)
const error = ref("")
let searchTimer: ReturnType<typeof setTimeout> | undefined

const query = computed(() => String(route.query.q ?? "").trim())

async function loadResults() {
  if (query.value.length < 2) {
    results.value = null
    loading.value = false
    return
  }

  loading.value = true
  error.value = ""
  try {
    const response = await api.get<GlobalSearchResults>("/discovery/search/", {
      params: { q: query.value },
    })
    results.value = response.data
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "La recherche est indisponible pour le moment.",
    )
  } finally {
    loading.value = false
  }
}

async function toggleFollow(user: UserProfile) {
  if (!auth.isAuthenticated) {
    await router.push({
      name: "login",
      query: { redirect: route.fullPath },
    })
    return
  }

  const response = user.is_following
    ? await api.delete<UserProfile>(`/users/${user.id}/follow/`)
    : await api.post<UserProfile>(`/users/${user.id}/follow/`)
  Object.assign(user, response.data)
  await auth.fetchMe()
}

watch(
  query,
  () => {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(loadResults, 220)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<template>
  <div class="container search-page">
    <section class="search-hero">
      <span class="eyebrow">Recherche globale</span>
      <h1>Trouve ta prochaine partie.</h1>
      <p>Recherche une liste publique, tes listes accessibles ou un joueur.</p>
      <SearchBar placeholder="Nom d’une liste, thème ou joueur…" />
    </section>

    <p v-if="query.length === 1" class="search-hint">
      Saisis au moins deux caractères.
    </p>
    <LoadingState v-else-if="loading" />
    <ErrorNotice v-else-if="error" :message="error" />

    <div v-else-if="results" class="search-results-stack">
      <section class="search-result-section">
        <div class="section-heading compact">
          <div>
            <span class="eyebrow">Listes</span>
            <h2>{{ results.lists.length }} résultat(s)</h2>
          </div>
        </div>
        <div v-if="results.lists.length" class="card-grid">
          <ListCard
            v-for="item in results.lists"
            :key="item.id"
            :item="item"
          />
        </div>
        <div v-else class="empty-panel">
          Aucune liste ne correspond à « {{ results.query }} ».
        </div>
      </section>

      <section class="search-result-section">
        <div class="section-heading compact">
          <div>
            <span class="eyebrow">Joueurs</span>
            <h2>{{ results.users.length }} résultat(s)</h2>
          </div>
        </div>
        <div v-if="results.users.length" class="player-grid">
          <article
            v-for="user in results.users"
            :key="user.id"
            class="player-card"
          >
            <div class="avatar avatar-small">
              {{ user.display_name.charAt(0).toUpperCase() }}
            </div>
            <div>
              <UserLink :user="user">
                <strong>{{ user.display_name }}</strong>
              </UserLink>
              <span>{{ user.follower_count }} abonnés</span>
            </div>
            <button
              class="button button-secondary button-small"
              @click="toggleFollow(user)"
            >
              {{
                auth.isAuthenticated
                  ? user.is_following
                    ? "Suivi"
                    : "Suivre"
                  : "Connexion"
              }}
            </button>
          </article>
        </div>
        <div v-else class="empty-panel">
          Aucun joueur ne correspond à « {{ results.query }} ».
        </div>
      </section>
    </div>
  </div>
</template>
