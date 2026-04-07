<script setup lang="ts">
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import type { Division } from "~/types";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const props = defineProps<{ divisions: Division[] }>();
const { TIER_BAR_COLORS } = useUtils();

const chartData = computed(() => {
  const items = props.divisions.slice(0, 20);
  return {
    labels: items.map((d) =>
      d.division.length > 14 ? d.division.substring(0, 14) + "…" : d.division
    ),
    datasets: [
      {
        label: "UAI Score",
        data: items.map((d) => parseFloat(d.uai_score.toFixed(3))),
        backgroundColor: items.map(
          (d) => TIER_BAR_COLORS[d.priority_tier] ?? "#999"
        ),
        borderRadius: 4,
      },
    ],
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        title: (_: any) => {
          const idx = _[0]?.dataIndex;
          return props.divisions[idx]?.division ?? "";
        },
        label: (ctx: any) => `UAI Score: ${ctx.parsed.y.toFixed(3)}`,
      },
    },
  },
  scales: {
    y: {
      min: 0,
      max: 1,
      ticks: { font: { size: 11 } },
    },
    x: {
      ticks: {
        font: { size: 10 },
        maxRotation: 45,
        minRotation: 45,
      },
    },
  },
};
</script>

<template>
  <div style="height: 320px">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
