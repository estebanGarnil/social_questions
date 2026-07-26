<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRoute } from "vue-router"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import LoadingState from "@/components/LoadingState.vue"
import UserLink from "@/components/UserLink.vue"
import type { PickQuestionResponse } from "@/types"
import { apiErrorMessage } from "@/utils/errors"

const route = useRoute()
const result = ref<PickQuestionResponse | null>(null)
const loading = ref(true)
const error = ref("")

const listId = computed(() => String(route.params.id))
const sessionPercentage = computed(() =>
  result.value ? Math.round(result.value.progress.percentage) : 0,
)

async function pickQuestion(restartSession = false) {
  loading.value = true
  error.value = ""
  try {
    const response = await api.post<PickQuestionResponse>(
      `/lists/${listId.value}/pick-random-question/`,
      { restart_session: restartSession },
    )
    result.value = response.data
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible de tirer une question.",
    )
  } finally {
    loading.value = false
  }
}

function nextQuestion() {
  void pickQuestion(result.value?.session_completed ?? false)
}

onMounted(() => {
  void pickQuestion(true)
})
</script>

<template>
  <div class="container play-page">
    <div class="play-topbar">
      <RouterLink
        class="back-link"
        :to="{ name: 'list-detail', params: { id: listId } }"
      >
        ← Quitter la partie
      </RouterLink>
      <span v-if="result" class="list-cycle-count">
        Liste : {{ result.list_progress.viewed_count }} /
        {{ result.list_progress.total_count }}
      </span>
    </div>

    <LoadingState v-if="loading && !result" />
    <ErrorNotice v-else-if="error && !result" :message="error" />

    <section
      v-else-if="result"
      class="play-stage"
      aria-live="polite"
      aria-atomic="true"
    >
      <div
        class="play-progress"
        role="progressbar"
        aria-label="Progression dans la série"
        :aria-valuenow="result.progress.viewed_count"
        aria-valuemin="0"
        :aria-valuemax="result.progress.total_count"
      >
        <span>
          {{ result.progress.viewed_count }} /
          {{ result.progress.total_count }}
        </span>
        <div class="progress-track">
          <span :style="{ width: `${sessionPercentage}%` }"></span>
        </div>
      </div>

      <img
        v-if="result.question.image"
        class="question-image"
        :src="result.question.image"
        alt=""
      />

      <span class="question-position">
        Question {{ result.progress.viewed_count }}
      </span>
      <h1>{{ result.question.text }}</h1>
      <p class="question-credit">
        Ajoutée par <UserLink :user="result.question.author" />
      </p>

      <div v-if="result.list_completed" class="notice notice-success">
        Tu as maintenant parcouru toute la liste.
      </div>
      <div
        v-else-if="result.session_completed"
        class="notice notice-session"
      >
        Cette série est terminée. Tu peux en lancer une nouvelle.
      </div>
      <ErrorNotice v-if="error" :message="error" />

      <button
        class="button button-primary play-button"
        :disabled="loading"
        @click="nextQuestion"
      >
        {{
          loading
            ? "Tirage…"
            : result.session_completed
              ? "Relancer une série"
              : "Question suivante"
        }}
      </button>
    </section>
  </div>
</template>
