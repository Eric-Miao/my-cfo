<script setup lang="ts">
import type { LatestGroupDetail } from "../api/client";

defineProps<{
  detail: LatestGroupDetail | null;
}>();
</script>

<template>
  <table v-if="detail?.members.length" class="detail-table">
    <thead>
      <tr>
        <th>Owner</th>
        <th>Assets</th>
        <th>Liabilities</th>
        <th>Net Worth</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="member in detail.members" :key="member.owner_id">
        <td>{{ member.owner_name }}</td>
        <td>{{ member.asset_total_official }}</td>
        <td>{{ member.liability_total_official }}</td>
        <td>{{ member.net_worth_official }}</td>
      </tr>
    </tbody>
  </table>
</template>
