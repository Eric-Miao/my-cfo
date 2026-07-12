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
import { onBeforeUnmount, onMounted, ref } from "vue";

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
]);

const chartElement = ref<HTMLDivElement | null>(null);
let chart: ECharts | null = null;

const metrics = [
  { label: "Net Worth", value: "$128,400", trend: "+4.2% MoM" },
  { label: "Monthly Cash Flow", value: "$3,250", trend: "+$640" },
  { label: "Investment Allocation", value: "68%", trend: "target 70%" },
];

onMounted(() => {
  if (!chartElement.value) {
    return;
  }

  chart = echarts.init(chartElement.value);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Income", "Expenses"] },
    grid: { left: 32, right: 16, top: 48, bottom: 28 },
    xAxis: { type: "category", data: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] },
    yAxis: { type: "value" },
    series: [
      { name: "Income", type: "line", data: [8200, 8400, 8300, 9100, 8800, 9300] },
      { name: "Expenses", type: "bar", data: [5100, 5300, 4900, 5700, 5400, 6050] },
    ],
  });
});

onBeforeUnmount(() => {
  chart?.dispose();
});
</script>

<template>
  <section class="metrics-grid">
    <article v-for="metric in metrics" :key="metric.label" class="metric-card">
      <span>{{ metric.label }}</span>
      <strong>{{ metric.value }}</strong>
      <small>{{ metric.trend }}</small>
    </article>
  </section>

  <section class="panel">
    <div class="panel-header">
      <div>
        <h2>Cash Flow Preview</h2>
        <p>Placeholder data until import and account specs are finalized.</p>
      </div>
    </div>
    <div ref="chartElement" class="chart" />
  </section>
</template>
