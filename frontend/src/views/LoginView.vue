<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  loading: boolean;
  error: string | null;
  t: (key: string) => string;
}>();

const emit = defineEmits<{
  login: [password: string];
}>();

const password = ref("");

function submitLogin() {
  emit("login", password.value);
}
</script>

<template>
  <main class="login-shell">
    <form class="login-card" @submit.prevent="submitLogin">
      <p class="eyebrow">My CFO</p>
      <h1>{{ props.t("auth.login") }}</h1>
      <label>
        <span>{{ props.t("auth.password") }}</span>
        <input v-model="password" type="password" autocomplete="current-password" />
      </label>
      <p v-if="props.error" class="notice">{{ props.t("auth.error") }}</p>
      <button type="submit" :disabled="props.loading">
        {{ props.t("auth.login") }}
      </button>
    </form>
  </main>
</template>
