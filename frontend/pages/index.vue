<script setup lang="ts">
const api = useApi();
const { pct } = useUtils();

const [{ data: stats }, { data: topDivisions }, { data: regions }] =
  await Promise.all([
    useAsyncData("stats", () => api.stats()),
    useAsyncData("top-divisions", () => api.topDivisions(20)),
    useAsyncData("regions", () => api.regions()),
  ]);
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-8">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">
        National Overview — Science & Math Teacher Capacity
      </h1>
      <p class="text-sm text-gray-500 mt-1">
        Aggregated regional intelligence for STAR capacity-building planning.
        All metrics are division-level — no individual teacher data is shown.
      </p>
    </div>

    <!-- Stats row -->
    <div
      v-if="stats"
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
    >
      <UiStatCard
        label="Critical Divisions"
        :value="stats.critical_divisions"
        sub="Needs immediate action"
        accent="red"
      />
      <UiStatCard
        label="High Priority"
        :value="stats.high_priority_divisions"
        sub="Elevated support needed"
        accent="amber"
      />
      <UiStatCard
        label="Standard Priority"
        :value="stats.standard_divisions"
        sub="Routine monitoring"
        accent="green"
      />
      <UiStatCard label="Total Divisions" :value="stats.total_divisions" accent="blue" />
      <UiStatCard
        label="Avg Mismatch Rate"
        :value="pct(stats.national_avg_mismatch_rate)"
        sub="Nationally"
      />
      <UiStatCard
        label="Avg NAT MPS"
        :value="`${stats.national_avg_nat_mps.toFixed(1)}%`"
        sub="Science + Math combined"
      />
    </div>

    <!-- UAI Bar Chart -->
    <div v-if="topDivisions" class="card p-6">
      <h2 class="section-title">Top 20 Underserved Divisions — UAI Score</h2>
      <div class="flex gap-4 text-xs mb-4">
        <span class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm bg-red-500 inline-block" />
          Critical Priority
        </span>
        <span class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm bg-amber-500 inline-block" />
          High Priority
        </span>
        <span class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm bg-green-500 inline-block" />
          Standard Priority
        </span>
      </div>
      <!-- .client.vue renders only in browser; ClientOnly wraps SSR fallback -->
      <ClientOnly>
        <ChartsUAIBar :divisions="topDivisions" />
        <template #fallback>
          <div class="h-80 flex items-center justify-center text-gray-400 text-sm">
            Loading chart…
          </div>
        </template>
      </ClientOnly>
    </div>

    <!-- Top 15 division cards -->
    <div v-if="topDivisions">
      <div class="flex items-center justify-between mb-4">
        <h2 class="section-title mb-0">Most Underserved Divisions</h2>
        <NuxtLink to="/divisions" class="text-sm text-[#1a4e8f] hover:underline">
          View all divisions →
        </NuxtLink>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <DashboardDivisionCard
          v-for="(d, i) in topDivisions.slice(0, 15)"
          :key="d.division"
          :division="d"
          :rank="i + 1"
        />
      </div>
    </div>

    <!-- Regional Heatmap -->
    <div v-if="regions" class="card p-6">
      <h2 class="section-title">Regional Capacity Heatmap</h2>
      <p class="text-xs text-gray-400 mb-4">
        Color intensity reflects relative gap severity. Red = high need, Green = lower need.
      </p>
      <ChartsRegionHeatmap :regions="regions" />
    </div>
  </div>
</template>
