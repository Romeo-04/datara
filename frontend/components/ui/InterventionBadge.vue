<script setup lang="ts">
const props = defineProps<{
  interventionKey: string;
  label: string;
}>();

const { INTERVENTION_COLORS } = useUtils();

const classes = computed(
  () => INTERVENTION_COLORS[props.interventionKey] ?? "bg-gray-100 text-gray-700"
);
</script>

<template>
  <span
    :class="`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${classes}`"
  >
    {{ label }}
  </span>
</template>
