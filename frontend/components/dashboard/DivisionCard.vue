<script setup lang="ts">
import type { Division } from "~/types";

defineProps<{
  division: Division;
  rank?: number;
}>();

const { pct, round2 } = useUtils();
</script>

<template>
  <div class="card p-4 hover:shadow-md transition-shadow">
    <!-- Header -->
    <div class="flex items-start justify-between gap-2 mb-3">
      <div>
        <div class="flex items-center gap-2">
          <span v-if="rank" class="text-xs font-bold text-gray-400 w-6">
            #{{ rank }}
          </span>
          <NuxtLink
            :to="`/divisions/${encodeURIComponent(division.division)}`"
            class="font-semibold text-[#1a4e8f] hover:underline text-sm"
          >
            {{ division.division }}
          </NuxtLink>
        </div>
        <div class="text-xs text-gray-500 mt-0.5 ml-8">{{ division.region }}</div>
      </div>
      <div class="flex flex-col items-end gap-1 shrink-0">
        <UiTierBadge :tier="division.priority_tier" />
        <span class="text-xs font-mono text-gray-500">
          UAI {{ round2(division.uai_score) }}
        </span>
      </div>
    </div>

    <!-- Factor mini-bars -->
    <div class="space-y-1 mb-3">
      <FactorBar label="Mismatch" :value="division.mismatch_rate" color="bg-purple-400" />
      <FactorBar label="Training Gap" :value="division.training_gap_rate" color="bg-blue-400" />
      <FactorBar label="Geo" :value="division.avg_geo_disadvantage" color="bg-teal-400" />
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between">
      <UiInterventionBadge
        :intervention-key="division.intervention.key"
        :label="division.intervention.label"
      />
      <span class="text-xs text-gray-400">
        {{ division.total_teachers }} teachers · {{ division.total_schools }} schools
      </span>
    </div>
  </div>
</template>

<!-- Inline sub-component for factor bars -->
<script lang="ts">
import { defineComponent, h } from "vue";

// Defined as a local component to avoid a separate file
const FactorBar = defineComponent({
  props: {
    label: String,
    value: Number,
    color: String,
  },
  setup(props) {
    const { pct } = useUtils();
    return () =>
      h("div", { class: "flex items-center gap-2" }, [
        h("span", { class: "text-xs text-gray-500 w-20 shrink-0" }, props.label),
        h("div", { class: "flex-1 bg-gray-100 rounded-full h-1.5" }, [
          h("div", {
            class: `${props.color} h-1.5 rounded-full`,
            style: { width: `${Math.min(100, (props.value ?? 0) * 100).toFixed(1)}%` },
          }),
        ]),
        h(
          "span",
          { class: "text-xs text-gray-500 w-10 text-right" },
          pct(props.value ?? 0)
        ),
      ]);
  },
});

export default {};
</script>
