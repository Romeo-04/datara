<script setup lang="ts">
const props = defineProps<{
  label: string;
  value: string | number;
  sub?: string;
  accent?: "red" | "amber" | "blue" | "green" | "default";
}>();

const accentClass = computed(() => {
  const map: Record<string, string> = {
    red: "border-l-4 border-red-500",
    amber: "border-l-4 border-amber-500",
    blue: "border-l-4 border-[#1a4e8f]",
    green: "border-l-4 border-green-500",
    default: "",
  };
  return map[props.accent ?? "default"];
});
</script>

<template>
  <div :class="`stat-card ${accentClass}`">
    <div class="text-2xl font-bold text-gray-900">{{ value }}</div>
    <div class="text-sm font-medium text-gray-600 mt-1">{{ label }}</div>
    <div v-if="sub" class="text-xs text-gray-400 mt-1">{{ sub }}</div>
  </div>
</template>
