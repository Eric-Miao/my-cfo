<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchHealth, type HealthResponse } from "./api/client";
import DashboardView from "./views/DashboardView.vue";

const health = ref<HealthResponse | null>(null);
const apiError = ref<string | null>(null);

onMounted(async () => {
  try {
    health.value = await fetchHealth();
  } catch (error) {
    apiError.value = error instanceof Error ? error.message : "API unavailable";
  }
});
</script>

<template>
  <main class="shell">
    <section class="hero">
      <div>
        <p class="eyebrow">Personal Finance Dashboard</p>
        <h1>My CFO</h1>
        <p class="lede">
          Track net worth, cash flow, spending, and portfolio allocation from a
          focused dashboard.
        </p>
      </div>
      <div class="api-status" :class="{ warning: apiError }">
        <span>API</span>
        <strong v-if="health">{{ health.status }}</strong>
        <strong v-else-if="apiError">offline</strong>
        <strong v-else>checking</strong>
      </div>
    </section>

    <p v-if="apiError" class="notice">
      Backend is not reachable yet: {{ apiError }}
    </p>

    <DashboardView />
  </main>
</template>
