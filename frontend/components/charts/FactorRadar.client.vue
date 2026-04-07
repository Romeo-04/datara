<script setup lang="ts">
import { Radar } from "vue-chartjs";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import type { Division } from "~/types";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const props = defineProps<{ division: Division }>();
const { FACTOR_LABELS } = useUtils();

const WEIGHTS: Record<string, number> = {
  mismatch: 0.3,
  training_gap: 0.25,
  geo_disadvantage: 0.2,
  staffing_pressure: 0.15,
  nat_gap: 0.1,
};

const chartData = computed(() => {
  const factors = props.division.factors;
  const keys = Object.keys(factors) as Array<keyof typeof factors>;

  return {
    labels: keys.map((k) => FACTOR_LABELS[k] ?? k),
    datasets: [
      {
        label: props.division.division,
        data: keys.map((k) => {
          const contrib = factors[k] as number;
          const weight = WEIGHTS[k] ?? 1;
          return parseFloat((contrib / weight).toFixed(3));
        }),
        backgroundColor: "rgba(26, 78, 143, 0.2)",
        borderColor: "#1a4e8f",
        pointBackgroundColor: "#1a4e8f",
        borderWidth: 2,
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
        label: (ctx: any) => `Score: ${ctx.parsed.r.toFixed(3)}`,
      },
    },
  },
  scales: {
    r: {
      min: 0,
      max: 1,
      ticks: { font: { size: 9 }, stepSize: 0.25 },
      pointLabels: { font: { size: 10 } },
    },
  },
};
</script>

<template>
  <div style="height: 260px">
    <Radar :data="chartData" :options="chartOptions" />
  </div>
</template>
