<script setup lang="ts">
const route = useRoute();
const api = useApi();
const { pct } = useUtils();

const regionName = decodeURIComponent(route.params.name as string);

const { data: divisions, error } = await useAsyncData(
  `region-divisions-${regionName}`,
  () => api.regionDivisions(regionName)
);

if (error.value || !divisions.value?.length) {
  throw createError({ statusCode: 404, message: `Region "${regionName}" not found` });
}

const totalTeachers = computed(() =>
  divisions.value!.reduce((s, d) => s + d.total_teachers, 0)
);
const totalSchools = computed(() =>
  divisions.value!.reduce((s, d) => s + d.total_schools, 0)
);
const avgMismatch = computed(
  () => divisions.value!.reduce((s, d) => s + d.mismatch_rate, 0) / divisions.value!.length
);
const avgTrainingGap = computed(
  () => divisions.value!.reduce((s, d) => s + d.training_gap_rate, 0) / divisions.value!.length
);
const avgNAT = computed(
  () => divisions.value!.reduce((s, d) => s + d.nat_combined_mps, 0) / divisions.value!.length
);
const criticalCount = computed(
  () => divisions.value!.filter((d) => d.priority_tier === "Critical Priority").length
);
</script>

<template>
  <div v-if="divisions" class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm text-gray-400 flex items-center gap-2">
      <NuxtLink to="/" class="hover:text-[#1a4e8f]">Dashboard</NuxtLink>
      <span>/</span>
      <NuxtLink to="/regions" class="hover:text-[#1a4e8f]">Regions</NuxtLink>
      <span>/</span>
      <span class="text-gray-700">{{ regionName }}</span>
    </div>

    <!-- Region header -->
    <div class="card p-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ regionName }}</h1>
      <p class="text-sm text-gray-500 mt-1">{{ divisions.length }} divisions</p>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
        <SummaryBox label="Total Teachers" :value="totalTeachers.toLocaleString()" />
        <SummaryBox label="Total Schools" :value="totalSchools.toLocaleString()" />
        <SummaryBox
          label="Avg Mismatch Rate"
          :value="pct(avgMismatch)"
          :highlight="avgMismatch > 0.35"
        />
        <SummaryBox
          label="Avg Training Gap"
          :value="pct(avgTrainingGap)"
          :highlight="avgTrainingGap > 0.4"
        />
        <SummaryBox
          label="Avg NAT MPS"
          :value="`${avgNAT.toFixed(1)}%`"
          :highlight="avgNAT < 45"
        />
      </div>

      <div
        v-if="criticalCount > 0"
        class="mt-4 bg-red-50 border border-red-200 rounded-lg px-4 py-2 text-sm text-red-700"
      >
        {{ criticalCount }} division{{ criticalCount > 1 ? "s" : "" }} in this region
        {{ criticalCount > 1 ? "are" : "is" }} flagged as Critical Priority.
      </div>
    </div>

    <!-- UAI Bar Chart -->
    <div class="card p-6">
      <h2 class="section-title">Division UAI Scores — {{ regionName }}</h2>
      <ClientOnly>
        <ChartsUAIBar :divisions="divisions" />
        <template #fallback>
          <div class="h-80 flex items-center justify-center text-gray-400 text-sm">
            Loading chart…
          </div>
        </template>
      </ClientOnly>
    </div>

    <!-- Division cards -->
    <div>
      <h2 class="section-title">Divisions by Priority Rank</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <DashboardDivisionCard
          v-for="d in divisions"
          :key="d.division"
          :division="d"
          :rank="d.priority_rank"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, h } from "vue";

const SummaryBox = defineComponent({
  props: { label: String, value: String, highlight: Boolean },
  setup(props) {
    return () =>
      h(
        "div",
        {
          class: `rounded-lg p-3 text-center ${props.highlight ? "bg-red-50" : "bg-gray-50"}`,
        },
        [
          h(
            "div",
            { class: `text-lg font-bold ${props.highlight ? "text-red-700" : "text-gray-900"}` },
            props.value
          ),
          h("div", { class: "text-xs text-gray-500 mt-0.5" }, props.label),
        ]
      );
  },
});

export default {};
</script>
