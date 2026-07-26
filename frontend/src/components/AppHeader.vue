<script setup lang="ts">
import { useRouter } from "vue-router"

import SearchBar from "@/components/SearchBar.vue"
import UserLink from "@/components/UserLink.vue"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  await router.push({ name: "home" })
}
</script>

<template>
  <header class="site-header">
    <div class="container header-inner">
      <RouterLink class="brand" :to="{ name: 'home' }">
        <span class="brand-mark">Q</span>
        <span>Questionly</span>
      </RouterLink>

      <SearchBar class="header-search" compact />

      <nav class="main-nav" aria-label="Navigation principale">
        <RouterLink :to="{ name: 'home' }">Découvrir</RouterLink>
        <RouterLink :to="{ name: 'search' }">Rechercher</RouterLink>
        <RouterLink
          v-if="auth.isAuthenticated"
          :to="{ name: 'list-create' }"
        >
          Créer une liste
        </RouterLink>
        <RouterLink
          v-if="auth.isAuthenticated"
          :to="{ name: 'profile' }"
        >
          Mon espace
        </RouterLink>
      </nav>

      <div class="header-actions">
        <template v-if="auth.isAuthenticated">
          <UserLink v-if="auth.user" class="user-pill" :user="auth.user">
            {{ auth.user.display_name }}
          </UserLink>
          <button class="button button-ghost button-small" @click="logout">
            Déconnexion
          </button>
        </template>
        <template v-else>
          <RouterLink class="button button-ghost button-small" :to="{ name: 'login' }">
            Connexion
          </RouterLink>
          <RouterLink class="button button-primary button-small" :to="{ name: 'register' }">
            S’inscrire
          </RouterLink>
        </template>
      </div>
    </div>

    <nav class="mobile-nav" aria-label="Navigation mobile">
      <RouterLink :to="{ name: 'home' }">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m3 11 9-8 9 8" />
          <path d="M5 10v10h14V10M9 20v-6h6v6" />
        </svg>
        Accueil
      </RouterLink>
      <RouterLink :to="{ name: 'search' }">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m16 16 5 5" />
        </svg>
        Recherche
      </RouterLink>
      <RouterLink
        v-if="auth.isAuthenticated"
        :to="{ name: 'list-create' }"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 4v16M4 12h16" />
        </svg>
        Créer
      </RouterLink>
      <RouterLink
        :to="{ name: auth.isAuthenticated ? 'profile' : 'login' }"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
        </svg>
        {{ auth.isAuthenticated ? "Profil" : "Connexion" }}
      </RouterLink>
    </nav>
  </header>
</template>
