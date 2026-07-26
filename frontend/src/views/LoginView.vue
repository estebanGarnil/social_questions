<script setup lang="ts">
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import ErrorNotice from "@/components/ErrorNotice.vue"
import { useAuthStore } from "@/stores/auth"
import { apiErrorMessage } from "@/utils/errors"

const email = ref("")
const password = ref("")
const loading = ref(false)
const error = ref("")
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

async function submit() {
  loading.value = true
  error.value = ""
  try {
    await auth.login(email.value, password.value)
    const redirect =
      typeof route.query.redirect === "string" ? route.query.redirect : "/"
    await router.push(redirect)
  } catch (requestError) {
    error.value = apiErrorMessage(
      requestError,
      "Adresse e-mail ou mot de passe incorrect.",
    )
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-card">
      <span class="eyebrow">Bon retour</span>
      <h1>Connexion</h1>
      <p>Retrouve tes listes, tes abonnements et ta progression.</p>

      <ErrorNotice v-if="error" :message="error" />

      <form class="form-stack" @submit.prevent="submit">
        <label>
          Adresse e-mail
          <input
            v-model="email"
            type="email"
            autocomplete="email"
            required
            placeholder="toi@exemple.fr"
          />
        </label>
        <label>
          Mot de passe
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            placeholder="••••••••••••"
          />
        </label>
        <button class="button button-primary button-full" :disabled="loading">
          {{ loading ? "Connexion…" : "Se connecter" }}
        </button>
      </form>

      <p class="auth-switch">
        Pas encore de compte ?
        <RouterLink :to="{ name: 'register' }">Créer un compte</RouterLink>
      </p>
    </section>
  </div>
</template>
