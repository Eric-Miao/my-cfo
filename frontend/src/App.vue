<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  fetchHealth,
  fetchMe,
  login,
  logout,
  type HealthResponse,
} from "./api/client";
import AppShell from "./components/AppShell.vue";
import { translate, type Locale } from "./i18n";
import { applyTheme, type ThemeMode } from "./theme/theme";
import DashboardView from "./views/DashboardView.vue";
import LoginView from "./views/LoginView.vue";

const health = ref<HealthResponse | null>(null);
const apiError = ref<string | null>(null);
const authenticated = ref(false);
const authLoading = ref(true);
const authError = ref<string | null>(null);
const locale = ref<Locale>("en-US");
const theme = ref<ThemeMode>("light");
const t = computed(() => (key: string) => translate(locale.value, key));

onMounted(async () => {
  try {
    health.value = await fetchHealth();
  } catch (error) {
    apiError.value = error instanceof Error ? error.message : "API unavailable";
  }

  applyTheme(theme.value);

  try {
    await fetchMe();
    authenticated.value = true;
  } catch {
    authenticated.value = false;
  } finally {
    authLoading.value = false;
  }
});

async function handleLogin(password: string) {
  authError.value = null;
  authLoading.value = true;
  try {
    await login(password);
    authenticated.value = true;
  } catch (error) {
    authError.value = error instanceof Error ? error.message : "Login failed";
  } finally {
    authLoading.value = false;
  }
}

async function handleLogout() {
  await logout();
  authenticated.value = false;
}

function toggleLocale() {
  locale.value = locale.value === "en-US" ? "zh-CN" : "en-US";
}

function toggleTheme() {
  theme.value = theme.value === "light" ? "dark" : "light";
  applyTheme(theme.value);
}
</script>

<template>
  <LoginView
    v-if="!authenticated"
    :loading="authLoading"
    :error="authError"
    :t="t"
    @login="handleLogin"
  />
  <AppShell
    v-else
    :locale="locale"
    :theme="theme"
    :t="t"
    @toggle-locale="toggleLocale"
    @toggle-theme="toggleTheme"
    @logout="handleLogout"
  >
    <div class="api-status" :class="{ warning: apiError }">
      <span>API</span>
      <strong v-if="health">{{ health.status }}</strong>
      <strong v-else-if="apiError">offline</strong>
      <strong v-else>checking</strong>
    </div>
    <p v-if="apiError" class="notice">
      Backend is not reachable yet: {{ apiError }}
    </p>
    <DashboardView :t="t" />
  </AppShell>
</template>
