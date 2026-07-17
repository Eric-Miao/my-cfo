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
import ChartCard from "../components/ChartCard.vue";
import FilterBar from "../components/FilterBar.vue";
import LatestGroupTable from "../components/LatestGroupTable.vue";
import MetricCard from "../components/MetricCard.vue";
import OwnerDashboardView from "./OwnerDashboardView.vue";

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
    <MetricCard
      v-for="metric in metrics"
      :key="metric.label"
      :label="metric.label"
      :value="metric.value"
      :unit="overview?.official_base_currency ?? 'CNY'"
    />
  </section>

  <FilterBar
    :display-currency="overview?.display_currency ?? 'CNY'"
    :estimate="overview?.display_values_are_estimates ?? false"
  />

  <ChartCard
    :title="props.t('dashboard.latestDetail')"
    :subtitle="overview?.current?.reporting_at"
  >
    <div ref="chartElement" class="chart" />
    <LatestGroupTable :detail="detail" />
  </ChartCard>

  <OwnerDashboardView title="Owner Dashboard" />
</template>
