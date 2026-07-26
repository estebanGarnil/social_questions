<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { api } from "@/api/http"
import ErrorNotice from "@/components/ErrorNotice.vue"
import LoadingState from "@/components/LoadingState.vue"
import UserLink from "@/components/UserLink.vue"
import { useAuthStore } from "@/stores/auth"
import type {
  Collaboration,
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
const collaborations = ref<Collaboration[]>([])
const questionDrafts = reactive<Record<string, string>>({})
const listForm = reactive({
  name: "",
  description: "",
  visibility: "private" as "public" | "private",
})
const newQuestion = ref("")
const newQuestionImage = ref<File | null>(null)
const collaboratorForm = reactive({
  email: "",
  role: "contributor" as "contributor" | "administrator",
})
const loading = ref(false)
const saving = ref(false)
const error = ref("")
const success = ref("")

const isNew = computed(() => !route.params.id)
const listId = computed(() => String(route.params.id ?? item.value?.id ?? ""))
const canAdminister = computed(() =>
  ["owner", "administrator"].includes(item.value?.current_user_role ?? ""),
)

function syncListForm(list: QuestionList) {
  listForm.name = list.name
  listForm.description = list.description
  listForm.visibility = list.visibility
}

async function loadRelatedData() {
  if (!listId.value) return
  const [questionsResponse, collaborationsResponse] = await Promise.all([
    api.get<PaginatedResponse<Question> | Question[]>(
      `/lists/${listId.value}/questions/`,
    ),
    api.get<PaginatedResponse<Collaboration> | Collaboration[]>(
      `/lists/${listId.value}/collaborators/`,
    ),
  ])
  questions.value = unwrapResults(questionsResponse.data)
  collaborations.value = unwrapResults(collaborationsResponse.data)
  questions.value.forEach((question) => {
    questionDrafts[question.id] = question.text
  })
}

async function load() {
  if (isNew.value) return
  loading.value = true
  try {
    const response = await api.get<QuestionList>(`/lists/${listId.value}/`)
    item.value = response.data
    syncListForm(response.data)
    await loadRelatedData()
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible de charger cette liste.",
    )
  } finally {
    loading.value = false
  }
}

async function saveList() {
  saving.value = true
  error.value = ""
  success.value = ""
  try {
    if (isNew.value) {
      const response = await api.post<QuestionList>("/lists/", listForm)
      item.value = response.data
      success.value = "La liste est créée. Tu peux maintenant ajouter des questions."
      await router.replace({
        name: "list-edit",
        params: { id: response.data.id },
      })
      await loadRelatedData()
    } else {
      const response = await api.patch<QuestionList>(
        `/lists/${listId.value}/`,
        listForm,
      )
      item.value = response.data
      success.value = "Les informations de la liste sont enregistrées."
    }
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible d’enregistrer la liste.",
    )
  } finally {
    saving.value = false
  }
}

function selectImage(event: Event) {
  const input = event.target as HTMLInputElement
  newQuestionImage.value = input.files?.[0] ?? null
}

async function addQuestion() {
  if (!newQuestion.value.trim()) return
  saving.value = true
  error.value = ""
  try {
    const formData = new FormData()
    formData.append("text", newQuestion.value.trim())
    if (newQuestionImage.value) {
      formData.append("image", newQuestionImage.value)
    }
    const response = await api.post<Question>(
      `/lists/${listId.value}/questions/`,
      formData,
    )
    questions.value.push(response.data)
    questionDrafts[response.data.id] = response.data.text
    newQuestion.value = ""
    newQuestionImage.value = null
    if (item.value) item.value.question_count += 1
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible d’ajouter la question.",
    )
  } finally {
    saving.value = false
  }
}

function canModifyQuestion(question: Question): boolean {
  return (
    canAdminister.value ||
    question.author.id === auth.user?.id
  )
}

async function updateQuestion(question: Question) {
  const text = questionDrafts[question.id]?.trim()
  if (!text) return
  const response = await api.patch<Question>(
    `/lists/${listId.value}/questions/${question.id}/`,
    { text },
  )
  Object.assign(question, response.data)
  success.value = "Question mise à jour."
}

async function deleteQuestion(question: Question) {
  if (!window.confirm("Supprimer cette question ?")) return
  await api.delete(`/lists/${listId.value}/questions/${question.id}/`)
  questions.value = questions.value.filter((item) => item.id !== question.id)
  if (item.value) item.value.question_count -= 1
}

async function addCollaborator() {
  saving.value = true
  error.value = ""
  try {
    const response = await api.post<Collaboration>(
      `/lists/${listId.value}/collaborators/`,
      collaboratorForm,
    )
    const existingIndex = collaborations.value.findIndex(
      (item) => item.id === response.data.id,
    )
    if (existingIndex >= 0) {
      collaborations.value[existingIndex] = response.data
    } else {
      collaborations.value.push(response.data)
    }
    collaboratorForm.email = ""
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible d’ajouter ce collaborateur.",
    )
  } finally {
    saving.value = false
  }
}

async function removeCollaborator(collaboration: Collaboration) {
  await api.delete(
    `/lists/${listId.value}/collaborators/${collaboration.id}/`,
  )
  collaborations.value = collaborations.value.filter(
    (item) => item.id !== collaboration.id,
  )
}

async function deleteList() {
  if (!window.confirm("Supprimer définitivement l’accès à cette liste ?")) return
  await api.delete(`/lists/${listId.value}/`)
  await router.push({ name: "profile" })
}

onMounted(load)
</script>

<template>
  <div class="container editor-page">
    <LoadingState v-if="loading" />
    <template v-else>
      <div class="page-title">
        <div>
          <span class="eyebrow">{{ isNew ? "Nouvelle création" : "Atelier collaboratif" }}</span>
          <h1>{{ isNew ? "Créer une liste" : "Modifier la liste" }}</h1>
        </div>
        <RouterLink
          v-if="item"
          class="button button-ghost"
          :to="{ name: 'list-detail', params: { id: item.id } }"
        >
          Voir la liste
        </RouterLink>
      </div>

      <ErrorNotice v-if="error" :message="error" />
      <div v-if="success" class="notice notice-success">{{ success }}</div>

      <section class="editor-panel">
        <div class="panel-heading">
          <div>
            <span class="step-number">01</span>
            <h2>Informations générales</h2>
          </div>
          <p>Le nom, la description et la visibilité de ta liste.</p>
        </div>
        <form class="form-stack" @submit.prevent="saveList">
          <label>
            Nom de la liste
            <input
              v-model="listForm.name"
              type="text"
              maxlength="200"
              required
              :disabled="Boolean(item && !canAdminister)"
              placeholder="Questions pour refaire le monde"
            />
          </label>
          <label>
            Description
            <textarea
              v-model="listForm.description"
              rows="4"
              :disabled="Boolean(item && !canAdminister)"
              placeholder="Explique en quelques mots ce que contient cette liste…"
            ></textarea>
          </label>
          <label>
            Visibilité
            <select
              v-model="listForm.visibility"
              :disabled="Boolean(item && !canAdminister)"
            >
              <option value="private">Privée</option>
              <option value="public">Publique</option>
            </select>
          </label>
          <button
            v-if="!item || canAdminister"
            class="button button-primary align-start"
            :disabled="saving"
          >
            {{ isNew ? "Créer la liste" : "Enregistrer" }}
          </button>
        </form>
      </section>

      <section v-if="item" class="editor-panel">
        <div class="panel-heading">
          <div>
            <span class="step-number">02</span>
            <h2>Questions</h2>
          </div>
          <p>Chaque contributeur garde le contrôle sur ses propres questions.</p>
        </div>

        <form class="question-add-form" @submit.prevent="addQuestion">
          <textarea
            v-model="newQuestion"
            rows="3"
            required
            placeholder="Écris une nouvelle question…"
          ></textarea>
          <div class="inline-actions">
            <label class="file-label">
              Ajouter une image
              <input type="file" accept="image/*" @change="selectImage" />
            </label>
            <button class="button button-primary" :disabled="saving">
              Ajouter
            </button>
          </div>
        </form>

        <div class="editable-question-list">
          <article v-for="(question, index) in questions" :key="question.id">
            <span class="question-index">{{ index + 1 }}</span>
            <div class="question-edit-body">
              <textarea
                v-model="questionDrafts[question.id]"
                rows="2"
                :disabled="!canModifyQuestion(question)"
              ></textarea>
              <small>Ajoutée par <UserLink :user="question.author" /></small>
            </div>
            <div v-if="canModifyQuestion(question)" class="stacked-actions">
              <button
                class="button button-secondary button-small"
                @click="updateQuestion(question)"
              >
                Enregistrer
              </button>
              <button
                class="button button-danger button-small"
                @click="deleteQuestion(question)"
              >
                Supprimer
              </button>
            </div>
          </article>
        </div>
      </section>

      <section v-if="item && canAdminister" class="editor-panel">
        <div class="panel-heading">
          <div>
            <span class="step-number">03</span>
            <h2>Collaborateurs</h2>
          </div>
          <p>Invite un utilisateur existant avec son adresse e-mail.</p>
        </div>

        <form class="collaborator-form" @submit.prevent="addCollaborator">
          <input
            v-model="collaboratorForm.email"
            type="email"
            required
            placeholder="collaborateur@exemple.fr"
          />
          <select v-model="collaboratorForm.role">
            <option value="contributor">Contributeur</option>
            <option value="administrator">Administrateur</option>
          </select>
          <button class="button button-primary" :disabled="saving">Ajouter</button>
        </form>

        <div class="people-list">
          <div v-for="collaboration in collaborations" :key="collaboration.id">
            <div>
              <UserLink :user="collaboration.user">
                <strong>{{ collaboration.user.display_name }}</strong>
              </UserLink>
              <span>{{ collaboration.role === "administrator" ? "Administrateur" : "Contributeur" }}</span>
            </div>
            <button
              class="button button-ghost button-small"
              @click="removeCollaborator(collaboration)"
            >
              Retirer
            </button>
          </div>
        </div>
      </section>

      <section v-if="item?.current_user_role === 'owner'" class="danger-zone">
        <div>
          <h2>Supprimer la liste</h2>
          <p>La liste disparaîtra du site, mais ses données historiques seront préservées.</p>
        </div>
        <button class="button button-danger" @click="deleteList">
          Supprimer
        </button>
      </section>
    </template>
  </div>
</template>
