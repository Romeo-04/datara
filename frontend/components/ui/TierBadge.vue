<script setup lang="ts">
const props = defineProps<{ tier: string }>();
const { TIER_COLORS } = useUtils();

const classes = computed(
  () =>
    TIER_COLORS[props.tier] ?? "bg-gray-100 text-gray-700 border-gray-300"
);
</script>

<template>
  <span
    :class="`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${classes}`"
  >
    {{ tier }}
  </span>
</template>
