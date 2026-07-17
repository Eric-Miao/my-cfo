<script setup lang="ts">
defineProps<{
  label: string;
  value: string;
  unit?: string;
}>();
</script>

<template>
  <article class="metric-card">
    <span>{{ label }}</span>
    <strong>{{ value }}</strong>
    <small v-if="unit">{{ unit }}</small>
  </article>
</template>
