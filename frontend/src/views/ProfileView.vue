<script setup lang="ts">
import { onMounted, ref } from "vue"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import ListCard from "@/components/ListCard.vue"
import LoadingState from "@/components/LoadingState.vue"
import UserLink from "@/components/UserLink.vue"
import { useAuthStore } from "@/stores/auth"
import type {
  PaginatedResponse,
  QuestionList,
  UserProfile,
} from "@/types"
import { unwrapResults } from "@/types"
import { apiErrorMessage } from "@/utils/errors"

const auth = useAuthStore()
const ownedLists = ref<QuestionList[]>([])
const following = ref<UserProfile[]>([])
const searchResults = ref<UserProfile[]>([])
const search = ref("")
const loading = ref(true)
const searching = ref(false)
const error = ref("")

async function load() {
  loading.value = true
  try {
    const [listsResponse, followingResponse] = await Promise.all([
      api.get<PaginatedResponse<QuestionList> | QuestionList[]>(
        "/lists/?scope=owned",
      ),
      api.get<UserProfile[]>("/users/following/"),
    ])
    ownedLists.value = unwrapResults(listsResponse.data)
    following.value = followingResponse.data
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible de charger ton espace.",
    )
  } finally {
    loading.value = false
  }
}

async function searchUsers() {
  if (!search.value.trim()) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    const response = await api.get<PaginatedResponse<UserProfile> | UserProfile[]>(
      "/users/",
      { params: { search: search.value.trim() } },
    )
    searchResults.value = unwrapResults(response.data)
  } finally {
    searching.value = false
  }
}

async function toggleFollow(user: UserProfile) {
  if (user.is_following) {
    const response = await api.delete<UserProfile>(`/users/${user.id}/follow/`)
    Object.assign(user, response.data)
    following.value = following.value.filter((item) => item.id !== user.id)
  } else {
    const response = await api.post<UserProfile>(`/users/${user.id}/follow/`)
    Object.assign(user, response.data)
    if (!following.value.some((item) => item.id === user.id)) {
      following.value.push(response.data)
    }
  }
  await auth.fetchMe()
}

onMounted(load)
</script>

<template>
  <div class="container profile-page">
    <LoadingState v-if="loading" />
    <ErrorNotice v-else-if="error" :message="error" />
    <template v-else>
      <section class="profile-hero">
        <div class="avatar">{{ auth.user?.display_name.charAt(0).toUpperCase() }}</div>
        <div>
          <span class="eyebrow">Mon espace</span>
          <h1>{{ auth.user?.display_name }}</h1>
          <p>{{ auth.user?.email }}</p>
        </div>
        <div class="profile-stats">
          <span><strong>{{ auth.user?.follower_count }}</strong> abonnés</span>
          <span><strong>{{ auth.user?.following_count }}</strong> suivis</span>
        </div>
      </section>

      <section class="profile-section">
        <div class="section-heading compact">
          <div>
            <span class="eyebrow">Mes créations</span>
            <h2>Mes listes</h2>
          </div>
          <RouterLink class="button button-primary" :to="{ name: 'list-create' }">
            Nouvelle liste
          </RouterLink>
        </div>
        <div v-if="ownedLists.length" class="card-grid">
          <ListCard v-for="item in ownedLists" :key="item.id" :item="item" />
        </div>
        <div v-else class="empty-panel">Tu n’as pas encore créé de liste.</div>
      </section>

      <section class="profile-section split-profile">
        <div>
          <div class="section-heading compact">
            <div>
              <span class="eyebrow">Abonnements</span>
              <h2>Personnes suivies</h2>
            </div>
          </div>
          <div class="people-list">
            <div v-for="user in following" :key="user.id">
              <div>
                <UserLink :user="user">
                  <strong>{{ user.display_name }}</strong>
                </UserLink>
                <span>{{ user.follower_count }} abonnés</span>
              </div>
              <button
                class="button button-ghost button-small"
                @click="toggleFollow(user)"
              >
                Ne plus suivre
              </button>
            </div>
            <div v-if="!following.length" class="empty-panel">
              Tu ne suis encore personne.
            </div>
          </div>
        </div>

        <div>
          <div class="section-heading compact">
            <div>
              <span class="eyebrow">Découvrir</span>
              <h2>Trouver un utilisateur</h2>
            </div>
          </div>
          <form class="search-form" @submit.prevent="searchUsers">
            <input
              v-model="search"
              type="search"
              placeholder="Rechercher par nom…"
            />
            <button class="button button-secondary" :disabled="searching">
              Rechercher
            </button>
          </form>
          <div class="people-list search-results">
            <div v-for="user in searchResults" :key="user.id">
              <div>
                <UserLink :user="user">
                  <strong>{{ user.display_name }}</strong>
                </UserLink>
                <span>{{ user.follower_count }} abonnés</span>
              </div>
              <button
                class="button button-primary button-small"
                @click="toggleFollow(user)"
              >
                {{ user.is_following ? "Suivi" : "Suivre" }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
