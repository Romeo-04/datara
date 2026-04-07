<script setup lang="ts">
const route = useRoute();
const api = useApi();
const { pct, round2, FACTOR_LABELS, FACTOR_COLORS } = useUtils();

const name = decodeURIComponent(route.params.name as string);

const { data: d, error } = await useAsyncData(`division-${name}`, () =>
  api.division(name)
);

if (error.value) {
  throw createError({ statusCode: 404, message: `Division "${name}" not found` });
}

const WEIGHTS: Record<string, number> = {
  mismatch: 0.3,
  training_gap: 0.25,
  geo_disadvantage: 0.2,
  staffing_pressure: 0.15,
  nat_gap: 0.1,
};

const factors = computed(() => {
  if (!d.value) return [];
  return (Object.keys(d.value.factors) as Array<keyof typeof d.value.factors>)
    .map((key, i) => ({
      key,
      label: FACTOR_LABELS[key] ?? key,
      value: d.value!.factors[key] as number,
      weight: WEIGHTS[key] ?? 1,
      color: FACTOR_COLORS[i],
      raw: rawValue(key),
    }))
    .sort((a, b) => b.value - a.value);
});

function rawValue(key: string): string {
  if (!d.value) return "";
  const map: Record<string, string> = {
    mismatch: pct(d.value.mismatch_rate),
    training_gap: pct(d.value.training_gap_rate),
    geo_disadvantage: round2(d.value.avg_geo_disadvantage),
    staffing_pressure: `${d.value.avg_ltr.toFixed(1)} LTR`,
    nat_gap: `${d.value.nat_combined_mps.toFixed(1)}% MPS`,
  };
  return map[key] ?? "";
}
</script>

<template>
  <div v-if="d" class="max-w-5xl mx-auto px-4 py-8 space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm text-gray-400 flex items-center gap-2">
      <NuxtLink to="/" class="hover:text-[#1a4e8f]">Dashboard</NuxtLink>
      <span>/</span>
      <NuxtLink to="/divisions" class="hover:text-[#1a4e8f]">Divisions</NuxtLink>
      <span>/</span>
      <span class="text-gray-700">{{ d.division }}</span>
    </div>

    <!-- Header card -->
    <div class="card p-6">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ d.division }}</h1>
          <p class="text-sm text-gray-500 mt-1">{{ d.region }}</p>
          <div class="flex items-center gap-3 mt-3">
            <UiTierBadge :tier="d.priority_tier" />
            <span class="text-sm text-gray-500">
              National Rank
              <span class="font-bold text-gray-800">#{{ d.priority_rank }}</span>
            </span>
            <span class="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded">
              UAI {{ round2(d.uai_score) }}
            </span>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3 text-center">
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <div class="text-xl font-bold text-gray-900">{{ d.total_teachers }}</div>
            <div class="text-xs text-gray-500">Teachers</div>
          </div>
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <div class="text-xl font-bold text-gray-900">{{ d.total_schools }}</div>
            <div class="text-xs text-gray-500">Schools</div>
          </div>
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <div class="text-xl font-bold text-gray-900">{{ d.avg_ltr.toFixed(1) }}</div>
            <div class="text-xs text-gray-500">Avg LTR</div>
          </div>
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <div class="text-xl font-bold text-gray-900">{{ d.nat_combined_mps.toFixed(1) }}%</div>
            <div class="text-xs text-gray-500">NAT MPS</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Factor breakdown + Radar -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Factor Breakdown -->
      <div class="card p-6">
        <h2 class="section-title">UAI Factor Breakdown</h2>
        <p class="text-xs text-gray-400 mb-4">
          Contribution of each factor to the overall Underserved Area Index score.
        </p>
        <div class="space-y-3">
          <div v-for="f in factors" :key="f.key">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-medium text-gray-700">{{ f.label }}</span>
              <div class="flex items-center gap-2 text-xs text-gray-500">
                <span>{{ f.raw }}</span>
                <span class="font-mono text-gray-400">+{{ f.value.toFixed(3) }}</span>
              </div>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all"
                :style="{
                  width: `${Math.min(100, (f.value / f.weight) * 100).toFixed(1)}%`,
                  backgroundColor: f.color,
                }"
              />
            </div>
            <div class="text-xs text-gray-400 mt-0.5">
              Weight: {{ (f.weight * 100).toFixed(0) }}% · Contribution: {{ f.value.toFixed(3) }}
            </div>
          </div>
        </div>
        <div class="mt-4 pt-3 border-t flex justify-between items-center">
          <span class="text-sm font-semibold text-gray-700">Total UAI Score</span>
          <span class="text-lg font-bold text-[#1a4e8f]">{{ round2(d.uai_score) }}</span>
        </div>
      </div>

      <!-- Radar Chart -->
      <div class="card p-6">
        <h2 class="section-title">Gap Profile Radar</h2>
        <p class="text-xs text-gray-400 mb-2">
          Normalized factor scores (0 = no gap, 1 = maximum gap).
        </p>
        <ClientOnly>
          <ChartsFactorRadar :division="d" />
          <template #fallback>
            <div class="h-64 flex items-center justify-center text-gray-400 text-sm">
              Loading chart…
            </div>
          </template>
        </ClientOnly>
      </div>
    </div>

    <!-- Explanation -->
    <div class="card p-6 border-l-4 border-[#1a4e8f]">
      <h2 class="section-title">System Explanation</h2>
      <p class="text-sm text-gray-700 leading-relaxed">{{ d.explanation }}</p>
    </div>

    <!-- Intervention recommendation -->
    <div class="card p-6">
      <h2 class="section-title">Recommended STAR Intervention</h2>
      <div class="mb-4">
        <UiInterventionBadge
          :intervention-key="d.intervention.key"
          :label="d.intervention.label"
        />
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div>
          <div class="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Description
          </div>
          <p class="text-gray-700">{{ d.intervention.description }}</p>
        </div>
        <div>
          <div class="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Delivery Mode
          </div>
          <p class="text-gray-700">{{ d.intervention.delivery }}</p>
        </div>
        <div>
          <div class="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Target Group
          </div>
          <p class="text-gray-700">{{ d.intervention.target }}</p>
        </div>
      </div>
    </div>

    <!-- Capacity metrics grid -->
    <div class="card p-6">
      <h2 class="section-title">Capacity Metrics</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <MetricBox label="Specialization Mismatch Rate" :value="pct(d.mismatch_rate)" :highlight="d.mismatch_rate > 0.35" />
        <MetricBox label="Training Coverage Gap" :value="pct(d.training_gap_rate)" :highlight="d.training_gap_rate > 0.4" />
        <MetricBox label="Novice Teacher Rate" :value="pct(d.novice_rate)" :highlight="d.novice_rate > 0.3" />
        <MetricBox label="Avg Years Experience" :value="d.avg_experience.toFixed(1)" />
        <MetricBox label="Avg Learner-Teacher Ratio" :value="d.avg_ltr.toFixed(1)" :highlight="d.avg_ltr > 45" />
        <MetricBox label="Geographic Disadvantage" :value="round2(d.avg_geo_disadvantage)" :highlight="d.avg_geo_disadvantage > 0.6" />
        <MetricBox label="NAT Science + Math MPS" :value="`${d.nat_combined_mps.toFixed(1)}%`" :highlight="d.nat_combined_mps < 45" />
        <MetricBox label="Priority Tier" :value="d.priority_tier" />
      </div>
    </div>

    <p class="text-xs text-gray-400 text-center">
      All metrics are aggregated at the division level.
      No individual teacher data is displayed or stored in this system.
    </p>
  </div>
</template>

<script lang="ts">
import { defineComponent, h } from "vue";

const MetricBox = defineComponent({
  props: { label: String, value: String, highlight: Boolean },
  setup(props) {
    return () =>
      h(
        "div",
        {
          class: `rounded-lg p-3 ${props.highlight ? "bg-red-50 border border-red-100" : "bg-gray-50"}`,
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
