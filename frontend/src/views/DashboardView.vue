<script setup lang="ts">
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import type { ECharts } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import {
  fetchHouseholdOverview,
  fetchLatestGroupDetail,
  type HouseholdOverview,
  type LatestGroupDetail,
} from "../api/client";

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
]);

const props = defineProps<{
  t: (key: string) => string;
}>();

const chartElement = ref<HTMLDivElement | null>(null);
const overview = ref<HouseholdOverview | null>(null);
const detail = ref<LatestGroupDetail | null>(null);
const dashboardError = ref<string | null>(null);
let chart: ECharts | null = null;

const metrics = computed(() => [
  {
    label: props.t("dashboard.netWorth"),
    value: overview.value?.current?.net_worth_official ?? "-",
  },
  {
    label: props.t("dashboard.totalAssets"),
    value: overview.value?.current?.total_assets_official ?? "-",
  },
  {
    label: props.t("dashboard.totalLiabilities"),
    value: overview.value?.current?.total_liabilities_official ?? "-",
  },
]);

onMounted(async () => {
  try {
    const [overviewResponse, detailResponse] = await Promise.all([
      fetchHouseholdOverview(),
      fetchLatestGroupDetail(),
    ]);
    overview.value = overviewResponse;
    detail.value = detailResponse;
  } catch (error) {
    dashboardError.value =
      error instanceof Error ? error.message : "Dashboard unavailable";
  }

  if (!chartElement.value) {
    return;
  }

  chart = echarts.init(chartElement.value);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Assets", "Liabilities"] },
    grid: { left: 32, right: 16, top: 48, bottom: 28 },
    xAxis: { type: "category", data: ["Latest"] },
    yAxis: { type: "value" },
    series: [
      {
        name: "Assets",
        type: "bar",
        data: [Number(overview.value?.current?.total_assets_official ?? 0)],
      },
      {
        name: "Liabilities",
        type: "bar",
        data: [Number(overview.value?.current?.total_liabilities_official ?? 0)],
      },
    ],
  });
});

onBeforeUnmount(() => {
  chart?.dispose();
});
</script>

<template>
  <p v-if="dashboardError" class="notice">{{ dashboardError }}</p>
  <p v-else-if="overview?.current === null" class="notice">
    {{ props.t("dashboard.empty") }}
  </p>

  <section id="household" class="metrics-grid">
    <article v-for="metric in metrics" :key="metric.label" class="metric-card">
      <span>{{ metric.label }}</span>
      <strong>{{ metric.value }}</strong>
      <small>{{ overview?.official_base_currency ?? "CNY" }}</small>
    </article>
  </section>

  <section class="panel">
    <div class="panel-header">
      <div>
        <h2>{{ props.t("dashboard.latestDetail") }}</h2>
        <p v-if="overview?.current">
          {{ overview.current.reporting_at }}
        </p>
      </div>
    </div>
    <div ref="chartElement" class="chart" />
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
  </section>
</template>
