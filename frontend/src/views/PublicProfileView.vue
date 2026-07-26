<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import ListCard from "@/components/ListCard.vue"
import LoadingState from "@/components/LoadingState.vue"
import { useAuthStore } from "@/stores/auth"
import type {
  PaginatedResponse,
  QuestionList,
  UserProfile,
} from "@/types"
import { unwrapResults } from "@/types"
import { apiErrorMessage } from "@/utils/errors"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const user = ref<UserProfile | null>(null)
const lists = ref<QuestionList[]>([])
const loading = ref(true)
const followLoading = ref(false)
const error = ref("")
const userId = computed(() => String(route.params.id))
const isOwnProfile = computed(() => auth.user?.id === user.value?.id)

async function load() {
  loading.value = true
  error.value = ""
  try {
    const [userResponse, listsResponse] = await Promise.all([
      api.get<UserProfile>(`/users/${userId.value}/`),
      api.get<PaginatedResponse<QuestionList> | QuestionList[]>(
        `/users/${userId.value}/lists/`,
      ),
    ])
    user.value = userResponse.data
    lists.value = unwrapResults(listsResponse.data)
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Ce profil est introuvable.",
    )
  } finally {
    loading.value = false
  }
}

async function toggleFollow() {
  if (!auth.isAuthenticated) {
    await router.push({
      name: "login",
      query: { redirect: route.fullPath },
    })
    return
  }
  if (!user.value) return

  followLoading.value = true
  try {
    const response = user.value.is_following
      ? await api.delete<UserProfile>(`/users/${user.value.id}/follow/`)
      : await api.post<UserProfile>(`/users/${user.value.id}/follow/`)
    user.value = response.data
    await auth.fetchMe()
  } finally {
    followLoading.value = false
  }
}

watch(userId, load)
onMounted(load)
</script>

<template>
  <div class="container public-profile-page">
    <LoadingState v-if="loading" />
    <ErrorNotice v-else-if="error" :message="error" />
    <template v-else-if="user">
      <header class="public-profile-header">
        <div class="avatar">
          {{ user.display_name.charAt(0).toUpperCase() }}
        </div>
        <div class="public-profile-identity">
          <span class="eyebrow">Profil</span>
          <h1>{{ user.display_name }}</h1>
          <div class="profile-stats">
            <span><strong>{{ user.follower_count }}</strong> abonnés</span>
            <span><strong>{{ user.following_count }}</strong> suivis</span>
          </div>
        </div>
        <button
          v-if="!isOwnProfile"
          class="button button-primary"
          :disabled="followLoading"
          @click="toggleFollow"
        >
          {{
            auth.isAuthenticated && user.is_following
              ? "Ne plus suivre"
              : "Suivre"
          }}
        </button>
      </header>

      <section class="public-profile-lists">
        <div class="section-heading compact">
          <div>
            <span class="eyebrow">Listes publiques</span>
            <h2>Créées par {{ user.display_name }}</h2>
          </div>
        </div>
        <div v-if="lists.length" class="card-grid">
          <ListCard v-for="item in lists" :key="item.id" :item="item" />
        </div>
        <div v-else class="empty-panel">
          Cet utilisateur n’a encore publié aucune liste.
        </div>
      </section>
    </template>
  </div>
</template>
