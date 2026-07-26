import { createRouter, createWebHistory } from "vue-router"

import { useAuthStore } from "@/stores/auth"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
    },
    {
      path: "/connexion",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/inscription",
      name: "register",
      component: () => import("@/views/RegisterView.vue"),
      meta: { guestOnly: true },
    },
    {
      path: "/recherche",
      name: "search",
      component: () => import("@/views/SearchView.vue"),
    },
    {
      path: "/listes/nouvelle",
      name: "list-create",
      component: () => import("@/views/ListEditorView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/listes/:id",
      name: "list-detail",
      component: () => import("@/views/ListDetailView.vue"),
    },
    {
      path: "/listes/:id/jouer",
      name: "list-play",
      component: () => import("@/views/PlayListView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/listes/:id/editer",
      name: "list-edit",
      component: () => import("@/views/ListEditorView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/profil",
      name: "profile",
      component: () => import("@/views/ProfileView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/utilisateurs/:id",
      name: "user-profile",
      component: () => import("@/views/PublicProfileView.vue"),
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return {
      name: "login",
      query: { redirect: to.fullPath },
    }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: "home" }
  }
  return true
})

export default router
