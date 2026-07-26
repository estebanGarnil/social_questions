<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import LoadingState from "@/components/LoadingState.vue"
import UserLink from "@/components/UserLink.vue"
import { useAuthStore } from "@/stores/auth"
import type {
  PaginatedResponse,
  Question,
  QuestionList,
} from "@/types"
import { unwrapResults } from "@/types"
import { apiErrorMessage } from "@/utils/errors"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const item = ref<QuestionList | null>(null)
const questions = ref<Question[]>([])
const loading = ref(true)
const error = ref("")
const actionLoading = ref(false)

const listId = computed(() => String(route.params.id))
const canEdit = computed(() =>
  ["owner", "administrator", "contributor"].includes(
    item.value?.current_user_role ?? "",
  ),
)

async function load() {
  loading.value = true
  try {
    const [listResponse, questionsResponse] = await Promise.all([
      api.get<QuestionList>(`/lists/${listId.value}/`),
      api.get<PaginatedResponse<Question> | Question[]>(
        `/lists/${listId.value}/questions/`,
      ),
    ])
    item.value = listResponse.data
    questions.value = unwrapResults(questionsResponse.data)
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Cette liste est introuvable ou privée.",
    )
  } finally {
    loading.value = false
  }
}

async function toggleSubscription() {
  if (!auth.isAuthenticated) {
    await router.push({
      name: "login",
      query: { redirect: route.fullPath },
    })
    return
  }
  if (!item.value) return

  actionLoading.value = true
  try {
    if (item.value.is_subscribed) {
      await api.delete(`/lists/${listId.value}/subscribe/`)
      item.value.is_subscribed = false
      item.value.subscriber_count -= 1
    } else {
      await api.post(`/lists/${listId.value}/subscribe/`)
      item.value.is_subscribed = true
      item.value.subscriber_count += 1
    }
  } finally {
    actionLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="container detail-page">
    <LoadingState v-if="loading" />
    <ErrorNotice v-else-if="error" :message="error" />
    <template v-else-if="item">
      <section class="detail-hero">
        <div class="detail-copy">
          <div class="card-topline">
            <span class="visibility-badge" :class="item.visibility">
              {{ item.visibility === "public" ? "Publique" : "Privée" }}
            </span>
            <span>Créée par <UserLink :user="item.owner" /></span>
          </div>
          <h1>{{ item.name }}</h1>
          <p>{{ item.description || "Cette liste n’a pas encore de description." }}</p>
          <div class="stats-row">
            <span><strong>{{ item.question_count }}</strong> questions</span>
            <span><strong>{{ item.visitor_count }}</strong> explorateurs</span>
            <span><strong>{{ item.subscriber_count }}</strong> abonnés</span>
          </div>
        </div>

        <div class="detail-actions">
          <RouterLink
            class="button button-primary"
            :class="{ disabled: item.question_count === 0 }"
            :to="{ name: 'list-play', params: { id: item.id } }"
          >
            Lancer jusqu’à 20 questions
          </RouterLink>
          <button
            class="button button-secondary"
            :disabled="actionLoading"
            @click="toggleSubscription"
          >
            {{ item.is_subscribed ? "Ne plus suivre" : "Suivre cette liste" }}
          </button>
          <RouterLink
            v-if="canEdit"
            class="button button-ghost"
            :to="{ name: 'list-edit', params: { id: item.id } }"
          >
            Modifier la liste
          </RouterLink>
        </div>
      </section>

      <section class="question-preview">
        <div class="section-heading compact">
          <div>
            <span class="eyebrow">Aperçu</span>
            <h2>Questions de la liste</h2>
            <p class="section-note">
              Chaque partie contient au maximum 20 questions. Relance une partie
              pour continuer une grande liste.
            </p>
          </div>
        </div>
        <ol v-if="questions.length" class="question-list">
          <li v-for="question in questions.slice(0, 6)" :key="question.id">
            <span>{{ question.text }}</span>
            <UserLink class="question-author" :user="question.author" />
          </li>
        </ol>
        <div v-else class="empty-panel">Cette liste ne contient encore aucune question.</div>
      </section>
    </template>
  </div>
</template>
