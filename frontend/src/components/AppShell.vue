<script setup lang="ts">
import type { Locale } from "../i18n";
import type { ThemeMode } from "../theme/theme";

defineProps<{
  locale: Locale;
  theme: ThemeMode;
  t: (key: string) => string;
}>();

const emit = defineEmits<{
  toggleLocale: [];
  toggleTheme: [];
  logout: [];
}>();
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Personal Finance Dashboard</p>
        <h1>{{ t("app.title") }}</h1>
        <p class="lede">{{ t("app.subtitle") }}</p>
      </div>
      <nav class="nav-actions" aria-label="Primary">
        <a href="#household">{{ t("nav.household") }}</a>
        <a href="#owners">{{ t("nav.owners") }}</a>
        <a href="#import">{{ t("nav.import") }}</a>
        <button type="button" @click="emit('toggleLocale')">
          {{ t("language.toggle") }}
        </button>
        <button type="button" @click="emit('toggleTheme')">
          {{ theme === "light" ? t("theme.dark") : t("theme.light") }}
        </button>
        <button type="button" @click="emit('logout')">
          {{ t("nav.logout") }}
        </button>
      </nav>
    </header>
    <slot />
  </main>
</template>
