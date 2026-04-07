<script setup lang="ts">
const api = useApi();
const { pct, normalize } = useUtils();

const { data: regions } = await useAsyncData("regions-page", () => api.regions());

const mismatchAll = computed(() => regions.value?.map((r) => r.avg_mismatch_rate) ?? []);
const geoAll = computed(() => regions.value?.map((r) => r.avg_geo_disadvantage) ?? []);
const natAll = computed(() => regions.value?.map((r) => r.avg_nat_combined_mps) ?? []);

function heatClass(value: number) {
  if (value >= 0.65) return "text-red-700 font-semibold";
  if (value >= 0.4) return "text-amber-700 font-semibold";
  return "text-green-700";
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Regional Overview</h1>
      <p class="text-sm text-gray-500 mt-1">
        {{ regions?.length ?? 0 }} regions · Aggregated from all division-level data
      </p>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-gray-50 border-b">
            <th class="text-left px-4 py-3 font-semibold text-gray-600">Region</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Divisions</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Teachers</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Schools</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Mismatch Rate</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Training Gap</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Novice Rate</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">Geo Score</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600">NAT MPS</th>
            <th class="text-center px-4 py-3 font-semibold text-gray-600"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in regions"
            :key="r.region"
            class="border-b hover:bg-gray-50 transition-colors"
          >
            <td class="px-4 py-3 font-medium text-gray-900">{{ r.region }}</td>
            <td class="px-4 py-3 text-center text-gray-500">{{ r.n_divisions }}</td>
            <td class="px-4 py-3 text-center text-gray-500">{{ r.total_teachers.toLocaleString() }}</td>
            <td class="px-4 py-3 text-center text-gray-500">{{ r.total_schools.toLocaleString() }}</td>
            <td :class="`px-4 py-3 text-center ${heatClass(normalize(r.avg_mismatch_rate, mismatchAll))}`">
              {{ pct(r.avg_mismatch_rate) }}
            </td>
            <td :class="`px-4 py-3 text-center ${heatClass(r.avg_training_gap_rate)}`">
              {{ pct(r.avg_training_gap_rate) }}
            </td>
            <td class="px-4 py-3 text-center text-gray-600">{{ pct(r.avg_novice_rate) }}</td>
            <td :class="`px-4 py-3 text-center ${heatClass(normalize(r.avg_geo_disadvantage, geoAll))}`">
              {{ r.avg_geo_disadvantage.toFixed(2) }}
            </td>
            <td :class="`px-4 py-3 text-center ${heatClass(normalize(Math.max(...natAll) - r.avg_nat_combined_mps, [0, Math.max(...natAll) - Math.min(...natAll)])  )}`">
              {{ r.avg_nat_combined_mps.toFixed(1) }}%
            </td>
            <td class="px-4 py-3 text-center">
              <NuxtLink
                :to="`/regions/${encodeURIComponent(r.region)}`"
                class="text-xs text-[#1a4e8f] hover:underline"
              >
                View →
              </NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="text-xs text-gray-400 text-center">
      Red = high need · Amber = elevated need · Green = lower need (relative to national distribution)
    </p>
  </div>
</template>
