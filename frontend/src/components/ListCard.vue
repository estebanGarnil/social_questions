<script setup lang="ts">
import UserLink from "@/components/UserLink.vue"
import type { QuestionList } from "@/types"

defineProps<{
  item: QuestionList
}>()
</script>

<template>
  <article class="list-card">
    <RouterLink
      class="list-card-main"
      :to="{ name: 'list-detail', params: { id: item.id } }"
    >
      <div class="card-topline">
        <span class="visibility-badge" :class="item.visibility">
          {{ item.visibility === "public" ? "Publique" : "Privée" }}
        </span>
        <span>{{ item.question_count }} questions</span>
      </div>

      <div>
        <h3>{{ item.name }}</h3>
        <p>{{ item.description || "Une liste à découvrir et à partager." }}</p>
      </div>
    </RouterLink>

    <div class="card-footer">
      <span>par <UserLink :user="item.owner" /></span>
      <span>{{ item.visitor_count }} explorateurs</span>
    </div>

    <div
      v-if="item.progress && item.progress.viewed_count > 0"
      class="mini-progress"
      :aria-label="`Progression : ${item.progress.percentage}%`"
    >
      <span :style="{ width: `${item.progress.percentage}%` }"></span>
    </div>
  </article>
</template>
