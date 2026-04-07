<script setup lang="ts">
import type { Region } from "~/types";

const props = defineProps<{ regions: Region[] }>();
const { pct, normalize } = useUtils();

const mismatchAll = computed(() => props.regions.map((r) => r.avg_mismatch_rate));
const geoAll = computed(() => props.regions.map((r) => r.avg_geo_disadvantage));
const natAll = computed(() => props.regions.map((r) => r.avg_nat_combined_mps));

function heatColor(value: number) {
  if (value >= 0.65) return "bg-red-500 text-white";
  if (value >= 0.4) return "bg-amber-400 text-gray-900";
  return "bg-green-400 text-gray-900";
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-gray-50">
          <th class="text-left px-3 py-2 font-semibold text-gray-600 border-b">Region</th>
          <th class="text-center px-3 py-2 font-semibold text-gray-600 border-b">Divisions</th>
          <th class="text-center px-3 py-2 font-semibold text-gray-600 border-b">Mismatch Rate</th>
          <th class="text-center px-3 py-2 font-semibold text-gray-600 border-b">Training Gap</th>
          <th class="text-center px-3 py-2 font-semibold text-gray-600 border-b">Geo Disadvantage</th>
          <th class="text-center px-3 py-2 font-semibold text-gray-600 border-b">NAT MPS</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in regions"
          :key="r.region"
          class="border-b hover:bg-gray-50 transition-colors"
        >
          <td class="px-3 py-2 font-medium">{{ r.region }}</td>
          <td class="px-3 py-2 text-center text-gray-500">{{ r.n_divisions }}</td>
          <td class="px-3 py-2 text-center">
            <span
              :class="`inline-block px-2 py-0.5 rounded text-xs font-semibold ${heatColor(normalize(r.avg_mismatch_rate, mismatchAll))}`"
            >
              {{ pct(r.avg_mismatch_rate) }}
            </span>
          </td>
          <td class="px-3 py-2 text-center">
            <span
              :class="`inline-block px-2 py-0.5 rounded text-xs font-semibold ${heatColor(r.avg_training_gap_rate)}`"
            >
              {{ pct(r.avg_training_gap_rate) }}
            </span>
          </td>
          <td class="px-3 py-2 text-center">
            <span
              :class="`inline-block px-2 py-0.5 rounded text-xs font-semibold ${heatColor(normalize(r.avg_geo_disadvantage, geoAll))}`"
            >
              {{ r.avg_geo_disadvantage.toFixed(2) }}
            </span>
          </td>
          <td class="px-3 py-2 text-center">
            <span
              :class="`inline-block px-2 py-0.5 rounded text-xs font-semibold ${heatColor(normalize(Math.max(...natAll) - r.avg_nat_combined_mps, [0, Math.max(...natAll) - Math.min(...natAll)]))}`"
            >
              {{ r.avg_nat_combined_mps.toFixed(1) }}%
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
