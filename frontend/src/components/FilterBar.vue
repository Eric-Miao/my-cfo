<script setup lang="ts">
defineProps<{
  displayCurrency: string;
  estimate: boolean;
}>();
</script>

<template>
  <div class="filter-bar">
    <span>{{ displayCurrency }}</span>
    <span v-if="estimate" class="badge">Estimate</span>
  </div>
</template>
