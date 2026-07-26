<script setup lang="ts">
import ListCard from "@/components/ListCard.vue"
import type { QuestionList } from "@/types"

defineProps<{
  eyebrow: string
  title: string
  description: string
  items: QuestionList[]
  emptyMessage?: string
}>()
</script>

<template>
  <section class="discovery-section">
    <div class="section-heading">
      <div>
        <span class="eyebrow">{{ eyebrow }}</span>
        <h2>{{ title }}</h2>
      </div>
      <p>{{ description }}</p>
    </div>

    <div v-if="items.length" class="card-grid">
      <ListCard v-for="item in items" :key="item.id" :item="item" />
    </div>
    <div v-else class="empty-panel">
      {{ emptyMessage || "Aucune liste à afficher pour le moment." }}
    </div>
  </section>
</template>
