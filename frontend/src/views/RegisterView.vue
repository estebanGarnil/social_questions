<script setup lang="ts">
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"

import ErrorNotice from "@/components/ErrorNotice.vue"
import { useAuthStore } from "@/stores/auth"
import { apiErrorMessage } from "@/utils/errors"

const form = reactive({
  display_name: "",
  email: "",
  password: "",
  password_confirm: "",
})
const loading = ref(false)
const error = ref("")
const auth = useAuthStore()
const router = useRouter()

async function submit() {
  if (form.password !== form.password_confirm) {
    error.value = "Les deux mots de passe ne correspondent pas."
    return
  }

  loading.value = true
  error.value = ""
  try {
    await auth.register(form)
    await router.push({ name: "home" })
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Impossible de créer le compte.",
    )
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-card auth-card-wide">
      <span class="eyebrow">Bienvenue</span>
      <h1>Créer un compte</h1>
      <p>Quelques secondes suffisent pour commencer à explorer.</p>

      <ErrorNotice v-if="error" :message="error" />

      <form class="form-stack" @submit.prevent="submit">
        <label>
          Nom affiché
          <input
            v-model="form.display_name"
            type="text"
            autocomplete="name"
            required
            maxlength="150"
            placeholder="Esteban"
          />
        </label>
        <label>
          Adresse e-mail
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            required
            placeholder="toi@exemple.fr"
          />
        </label>
        <div class="form-columns">
          <label>
            Mot de passe
            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              required
              placeholder="8 caractères minimum"
            />
          </label>
          <label>
            Confirmation
            <input
              v-model="form.password_confirm"
              type="password"
              autocomplete="new-password"
              required
              placeholder="Répète le mot de passe"
            />
          </label>
        </div>
        <button class="button button-primary button-full" :disabled="loading">
          {{ loading ? "Création…" : "Créer mon compte" }}
        </button>
      </form>

      <p class="auth-switch">
        Déjà inscrit ?
        <RouterLink :to="{ name: 'login' }">Se connecter</RouterLink>
      </p>
    </section>
  </div>
</template>
