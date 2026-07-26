<script setup lang="ts">
import { onMounted, ref } from "vue"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import ListSection from "@/components/ListSection.vue"
import LoadingState from "@/components/LoadingState.vue"
import SearchBar from "@/components/SearchBar.vue"
import UserLink from "@/components/UserLink.vue"
import { useAuthStore } from "@/stores/auth"
import type { DiscoveryHome } from "@/types"
import { apiErrorMessage } from "@/utils/errors"

const auth = useAuthStore()
const discovery = ref<DiscoveryHome | null>(null)
const loading = ref(true)
const error = ref("")

async function loadHome() {
  loading.value = true
  error.value = ""
  try {
    const response = await api.get<DiscoveryHome>("/discovery/home/")
    discovery.value = response.data
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible de charger les listes pour le moment.",
    )
  } finally {
    loading.value = false
  }
}

onMounted(loadHome)
</script>

<template>
  <div class="home-page">
    <section class="container home-search">
      <h1>Rechercher</h1>
      <SearchBar placeholder="Une liste, un thème ou une personne…" />
    </section>

    <div class="container page-stack">
      <LoadingState v-if="loading" />
      <ErrorNotice v-else-if="error" :message="error" />
      <template v-else-if="discovery">
        <ListSection
          v-if="auth.isAuthenticated"
          eyebrow="Abonnements"
          title="Listes suivies"
          description="Les listes auxquelles tu es abonné."
          :items="discovery.followed_lists"
          empty-message="Tu ne suis encore aucune liste."
        />

        <section v-if="auth.isAuthenticated" class="discovery-section">
          <div class="section-heading">
            <div>
              <span class="eyebrow">Abonnements</span>
              <h2>Personnes suivies</h2>
            </div>
            <p>Accède directement aux profils que tu suis.</p>
          </div>

          <div v-if="discovery.followed_users.length" class="player-grid">
            <article
              v-for="user in discovery.followed_users"
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
              <UserLink class="button button-ghost button-small" :user="user">
                Voir
              </UserLink>
            </article>
          </div>
          <div v-else class="empty-panel">
            Tu ne suis encore personne.
          </div>
        </section>

        <ListSection
          eyebrow="Découverte"
          title="Listes à découvrir"
          description="Des listes publiques populaires que tu n’as pas encore parcourues."
          :items="discovery.discover"
        />
      </template>
    </div>
  </div>
</template>
