<script setup lang="ts">
const route = useRoute();
const api = useApi();
const { pct } = useUtils();

const TIERS = ["Critical Priority", "High Priority", "Standard Priority"];

// Reactive filter state driven by query params
const page = computed(() => Number(route.query.page ?? 1));
const regionFilter = computed(() => (route.query.region as string) ?? "");
const tierFilter = computed(() => (route.query.tier as string) ?? "");
const searchFilter = computed(() => (route.query.search as string) ?? "");

const { data: divisionsData, refresh } = await useAsyncData(
  "divisions-list",
  () =>
    api.divisions({
      page: page.value,
      page_size: 24,
      region: regionFilter.value || undefined,
      tier: tierFilter.value || undefined,
      search: searchFilter.value || undefined,
    }),
  { watch: [page, regionFilter, tierFilter, searchFilter] }
);

const { data: regions } = await useAsyncData("regions-for-filter", () =>
  api.regions()
);

const totalPages = computed(() =>
  divisionsData.value ? Math.ceil(divisionsData.value.total / 24) : 1
);

// Local form state
const searchInput = ref(searchFilter.value);
const regionInput = ref(regionFilter.value);
const tierInput = ref(tierFilter.value);

const router = useRouter();

function applyFilters() {
  router.push({
    path: "/divisions",
    query: {
      ...(searchInput.value ? { search: searchInput.value } : {}),
      ...(regionInput.value ? { region: regionInput.value } : {}),
      ...(tierInput.value ? { tier: tierInput.value } : {}),
      page: 1,
    },
  });
}

function clearFilters() {
  searchInput.value = "";
  regionInput.value = "";
  tierInput.value = "";
  router.push("/divisions");
}

function goPage(p: number) {
  router.push({
    path: "/divisions",
    query: { ...route.query, page: p },
  });
}

const hasFilters = computed(
  () => searchFilter.value || regionFilter.value || tierFilter.value
);
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">All Divisions</h1>
      <p class="text-sm text-gray-500 mt-1">
        {{ divisionsData?.total ?? 0 }} divisions ranked by Underserved Area Index
      </p>
    </div>

    <!-- Filters -->
    <div class="card p-4">
      <div class="flex flex-wrap gap-3 items-center">
        <input
          v-model="searchInput"
          type="text"
          placeholder="Search division or region…"
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a4e8f]"
          @keyup.enter="applyFilters"
        />
        <select
          v-model="regionInput"
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a4e8f]"
        >
          <option value="">All Regions</option>
          <option v-for="r in regions" :key="r.region" :value="r.region">
            {{ r.region }}
          </option>
        </select>
        <select
          v-model="tierInput"
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a4e8f]"
        >
          <option value="">All Tiers</option>
          <option v-for="t in TIERS" :key="t" :value="t">{{ t }}</option>
        </select>
        <button
          class="bg-[#1a4e8f] text-white text-sm px-4 py-1.5 rounded-lg hover:bg-blue-800 transition-colors"
          @click="applyFilters"
        >
          Filter
        </button>
        <button
          v-if="hasFilters"
          class="text-sm text-gray-400 hover:text-gray-600"
          @click="clearFilters"
        >
          Clear filters
        </button>
      </div>
    </div>

    <!-- Tier count badges -->
    <div class="flex gap-3 flex-wrap">
      <span
        v-for="t in TIERS"
        :key="t"
        class="flex items-center gap-1 text-xs text-gray-500"
      >
        <UiTierBadge :tier="t" />
        {{ divisionsData?.results.filter((d) => d.priority_tier === t).length ?? 0 }} shown
      </span>
    </div>

    <!-- Division cards grid -->
    <div
      v-if="divisionsData?.results.length"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <DashboardDivisionCard
        v-for="d in divisionsData.results"
        :key="d.division"
        :division="d"
        :rank="d.priority_rank"
      />
    </div>
    <div v-else class="text-center py-16 text-gray-400">
      No divisions match the current filters.
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center gap-2 pt-4">
      <button
        v-if="page > 1"
        class="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50"
        @click="goPage(page - 1)"
      >
        Previous
      </button>
      <span class="px-4 py-2 text-sm text-gray-500">
        Page {{ page }} of {{ totalPages }}
      </span>
      <button
        v-if="page < totalPages"
        class="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50"
        @click="goPage(page + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>
