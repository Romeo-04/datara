<script setup lang="ts">
const api = useApi();

const [{ data: regions }, { data: divisions }] = await Promise.all([
  useAsyncData("map-regions", () => api.regions()),
  useAsyncData("map-divisions", () => api.topDivisions(50)),
]);

const criticalDivisions = computed(() =>
  (divisions.value ?? [])
    .filter((d) => d.priority_tier === "Critical Priority")
    .slice(0, 10)
);

const tierCounts = computed(() => ({
  critical: (divisions.value ?? []).filter((d) => d.priority_tier === "Critical Priority").length,
  high: (divisions.value ?? []).filter((d) => d.priority_tier === "High Priority").length,
  standard: (divisions.value ?? []).filter((d) => d.priority_tier === "Standard Priority").length,
}));

const regionsSortedByUAI = computed(() =>
  [...(regions.value ?? [])].sort((a, b) => (b.avg_uai_score ?? 0) - (a.avg_uai_score ?? 0))
);
</script>

<template>
  <div class="flex h-[calc(100vh-56px)] overflow-hidden">

    <!-- Map -->
    <div class="flex-1 relative">
      <MapPhilippinesMap
        v-if="regions && divisions"
        :regions="regions"
        :divisions="divisions"
      />

      <!-- Title overlay -->
      <div class="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/90 backdrop-blur
                  border border-gray-200 rounded-xl px-5 py-2 shadow text-center pointer-events-none">
        <div class="font-bold text-[#1a4e8f] text-sm">Philippines — STAR Underserved Area Map</div>
        <div class="text-xs text-gray-500">Click a region circle for details · Zoom in for division view</div>
      </div>
    </div>

    <!-- Side panel -->
    <div class="w-72 bg-white border-l border-gray-200 flex flex-col overflow-hidden shadow-lg">

      <!-- Header -->
      <div class="p-4 border-b bg-[#1a4e8f] text-white">
        <div class="font-bold text-sm">Priority Summary</div>
        <div class="text-xs text-blue-200 mt-0.5">All {{ (divisions ?? []).length }} divisions</div>
      </div>

      <!-- Tier counts -->
      <div class="p-4 border-b grid grid-cols-3 gap-2 text-center text-xs">
        <div class="bg-red-50 rounded-lg p-2">
          <div class="text-xl font-bold text-red-600">{{ tierCounts.critical }}</div>
          <div class="text-gray-500 mt-0.5">Critical</div>
        </div>
        <div class="bg-amber-50 rounded-lg p-2">
          <div class="text-xl font-bold text-amber-600">{{ tierCounts.high }}</div>
          <div class="text-gray-500 mt-0.5">High</div>
        </div>
        <div class="bg-green-50 rounded-lg p-2">
          <div class="text-xl font-bold text-green-600">{{ tierCounts.standard }}</div>
          <div class="text-gray-500 mt-0.5">Standard</div>
        </div>
      </div>

      <!-- Top critical divisions -->
      <div class="px-4 pt-3 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Top Critical Divisions
      </div>
      <div class="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
        <NuxtLink
          v-for="d in criticalDivisions"
          :key="d.division"
          :to="`/divisions/${encodeURIComponent(d.division)}`"
          class="block p-3 rounded-lg border border-red-100 bg-red-50 hover:bg-red-100 transition-colors"
        >
          <div class="flex items-center justify-between mb-1">
            <span class="font-semibold text-sm text-gray-800">{{ d.division }}</span>
            <span class="text-xs font-mono text-red-700">{{ d.uai_score.toFixed(3) }}</span>
          </div>
          <div class="text-xs text-gray-500 mb-1.5">{{ d.region }}</div>
          <div class="w-full bg-red-200 rounded-full h-1.5">
            <div
              class="bg-red-500 h-1.5 rounded-full"
              :style="{ width: `${(d.uai_score * 100).toFixed(1)}%` }"
            />
          </div>
          <div class="flex justify-between text-xs text-gray-400 mt-1">
            <span>Rank #{{ d.priority_rank }}</span>
            <span>{{ d.total_teachers }} teachers</span>
          </div>
        </NuxtLink>

        <NuxtLink
          to="/divisions?tier=Critical+Priority"
          class="block text-center text-xs text-[#1a4e8f] hover:underline pt-1"
        >
          View all critical divisions →
        </NuxtLink>
      </div>

      <!-- Regions by UAI -->
      <div class="border-t px-4 pt-3 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Regions by Avg UAI
      </div>
      <div class="overflow-y-auto max-h-52 px-3 pb-3 space-y-1">
        <NuxtLink
          v-for="r in regionsSortedByUAI"
          :key="r.region"
          :to="`/regions/${encodeURIComponent(r.region)}`"
          class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <span class="text-xs text-gray-700">{{ r.region }}</span>
          <div class="flex items-center gap-2">
            <div class="w-16 bg-gray-100 rounded-full h-1.5">
              <div
                class="h-1.5 rounded-full"
                :style="{
                  width: `${((r.avg_uai_score ?? 0) * 100).toFixed(1)}%`,
                  backgroundColor: (r.avg_uai_score ?? 0) >= 0.65 ? '#c0392b'
                    : (r.avg_uai_score ?? 0) >= 0.4 ? '#e67e22' : '#27ae60',
                }"
              />
            </div>
            <span class="text-xs font-mono text-gray-500 w-10 text-right">
              {{ (r.avg_uai_score ?? 0).toFixed(3) }}
            </span>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
