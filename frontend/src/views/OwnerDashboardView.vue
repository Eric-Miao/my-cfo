<script setup lang="ts">
defineProps<{
  title: string;
}>();
</script>

<template>
  <section id="owners" class="panel">
    <div class="panel-header">
      <h2>{{ title }}</h2>
      <p>Owner-level trend data is sourced from finalized household groups.</p>
    </div>
  </section>
</template>
