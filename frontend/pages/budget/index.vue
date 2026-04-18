<script setup lang="ts">
const { apiUrl } = useApi();

const { data, pending, error } = await useAsyncData("budget", () =>
  $fetch<any>(apiUrl("/api/v1/budget"))
);

const TIER_CONFIG: Record<string, { color: string; bg: string; border: string; icon: string }> = {
  "Critical Priority": { color: "text-red-600",    bg: "bg-red-50",    border: "border-red-200",   icon: "🔴" },
  "High Priority":     { color: "text-amber-600",  bg: "bg-amber-50",  border: "border-amber-200", icon: "🟠" },
  "Standard Priority": { color: "text-green-600",  bg: "bg-green-50",  border: "border-green-200", icon: "🟢" },
};

const BREAKDOWN_LABELS: Record<string, string> = {
  materials:   "Training Materials & Modules",
  facilitator: "Facilitator / Trainer Fees",
  logistics:   "Travel & Logistics",
  lodging:     "Board & Lodging",
  overhead:    "Administrative Overhead",
};

const BREAKDOWN_COLORS: Record<string, string> = {
  materials:   "bg-blue-400",
  facilitator: "bg-purple-400",
  logistics:   "bg-amber-400",
  lodging:     "bg-green-400",
  overhead:    "bg-gray-400",
};

function peso(n: number) {
  return "₱" + Number(n).toLocaleString("en-PH", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function pesoShort(n: number) {
  if (n >= 1_000_000_000) return `₱${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000)     return `₱${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)         return `₱${(n / 1_000).toFixed(1)}K`;
  return peso(n);
}

const expandedDivision = ref<string | null>(null);
const divisionSearch   = ref("");
const tierFilter       = ref("All");

const filteredDivisions = computed(() => {
  if (!data.value) return [];
  return data.value.divisions.filter((d: any) => {
    const matchSearch = d.division.toLowerCase().includes(divisionSearch.value.toLowerCase()) ||
                        d.region.toLowerCase().includes(divisionSearch.value.toLowerCase());
    const matchTier   = tierFilter.value === "All" || d.priority_tier === tierFilter.value;
    return matchSearch && matchTier;
  });
});

const maxRegionCost = computed(() =>
  data.value ? Math.max(...data.value.by_region.map((r: any) => r.total)) : 1
);
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-8">

    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-[#1a4e8f]">STAR Program Budget Estimator</h1>
      <p class="text-sm text-gray-500 mt-1">
        Estimated financial requirements for deploying STAR interventions across all divisions.
        Costs are modelled per teacher and school, adjusted for geographic remoteness.
      </p>
    </div>

    <div v-if="pending" class="text-center py-20 text-gray-400">Loading estimates…</div>
    <div v-else-if="error" class="text-center py-20 text-red-500">Failed to load budget data.</div>

    <template v-else-if="data">

      <!-- ── National summary cards ─────────────────────────────────── -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Grand total -->
        <div class="col-span-1 sm:col-span-2 lg:col-span-1 bg-[#1a4e8f] text-white rounded-2xl p-5 shadow">
          <div class="text-xs font-semibold uppercase tracking-wide text-blue-200 mb-1">Total Estimated Budget</div>
          <div class="text-3xl font-bold">{{ pesoShort(data.grand_total) }}</div>
          <div class="text-xs text-blue-200 mt-1">{{ data.divisions.length }} divisions nationwide</div>
        </div>

        <!-- Per tier -->
        <div
          v-for="(tier, name) in data.by_tier"
          :key="name"
          :class="['rounded-2xl p-5 shadow border', TIER_CONFIG[name]?.bg, TIER_CONFIG[name]?.border]"
        >
          <div class="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
            {{ TIER_CONFIG[name]?.icon }} {{ name }}
          </div>
          <div :class="['text-2xl font-bold', TIER_CONFIG[name]?.color]">{{ pesoShort(tier.total) }}</div>
          <div class="text-xs text-gray-500 mt-1">
            {{ tier.divisions }} divisions · {{ tier.teachers.toLocaleString() }} teachers
          </div>
        </div>
      </div>

      <!-- ── Intervention breakdown ─────────────────────────────────── -->
      <div class="bg-white rounded-2xl shadow border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b bg-gray-50">
          <h2 class="font-bold text-[#1a4e8f]">Breakdown by Intervention Package</h2>
          <p class="text-xs text-gray-400 mt-0.5">Line-item estimates per package type</p>
        </div>
        <div class="divide-y">
          <div v-for="inv in data.by_intervention" :key="inv.key" class="px-6 py-4">
            <div class="flex items-start justify-between gap-4 mb-3">
              <div>
                <div class="font-semibold text-gray-800 text-sm">{{ inv.label }}</div>
                <div class="text-xs text-gray-400 mt-0.5">
                  {{ inv.divisions }} divisions · {{ inv.teachers.toLocaleString() }} teachers · {{ inv.schools }} schools
                </div>
              </div>
              <div class="text-right shrink-0">
                <div class="font-bold text-[#1a4e8f] text-lg">{{ pesoShort(inv.total) }}</div>
                <div class="text-xs text-gray-400">{{ ((inv.total / data.grand_total) * 100).toFixed(1) }}% of total</div>
              </div>
            </div>

            <!-- Stacked bar -->
            <div class="flex h-3 rounded-full overflow-hidden mb-2 bg-gray-100">
              <div
                v-for="(key) in Object.keys(BREAKDOWN_COLORS)"
                :key="key"
                :class="BREAKDOWN_COLORS[key]"
                :style="{ width: `${((inv.breakdown[key] / inv.total) * 100).toFixed(1)}%` }"
                :title="`${BREAKDOWN_LABELS[key]}: ${peso(inv.breakdown[key])}`"
              />
            </div>

            <!-- Line items -->
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-2">
              <div v-for="key in Object.keys(BREAKDOWN_COLORS)" :key="key" class="text-center">
                <div class="flex items-center justify-center gap-1 mb-0.5">
                  <span :class="['w-2 h-2 rounded-full inline-block', BREAKDOWN_COLORS[key]]" />
                  <span class="text-xs text-gray-500">{{ BREAKDOWN_LABELS[key].split(' ')[0] }}</span>
                </div>
                <div class="text-xs font-semibold text-gray-700">{{ pesoShort(inv.breakdown[key]) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Legend -->
        <div class="px-6 py-3 bg-gray-50 border-t flex flex-wrap gap-4">
          <div v-for="key in Object.keys(BREAKDOWN_COLORS)" :key="key" class="flex items-center gap-1.5 text-xs text-gray-500">
            <span :class="['w-3 h-3 rounded-sm inline-block', BREAKDOWN_COLORS[key]]" />
            {{ BREAKDOWN_LABELS[key] }}
          </div>
        </div>
      </div>

      <!-- ── Regional breakdown ─────────────────────────────────────── -->
      <div class="bg-white rounded-2xl shadow border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b bg-gray-50">
          <h2 class="font-bold text-[#1a4e8f]">Budget Allocation by Region</h2>
        </div>
        <div class="px-6 py-4 space-y-3">
          <div v-for="r in data.by_region" :key="r.region" class="flex items-center gap-3">
            <div class="w-28 text-xs text-gray-600 font-medium shrink-0 truncate">{{ r.region }}</div>
            <div class="flex-1 bg-gray-100 rounded-full h-5 relative overflow-hidden">
              <div
                class="h-full bg-[#1a4e8f] rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                :style="{ width: `${(r.total / maxRegionCost * 100).toFixed(1)}%`, minWidth: '4rem' }"
              >
                <span class="text-white text-xs font-semibold">{{ pesoShort(r.total) }}</span>
              </div>
            </div>
            <div class="w-20 text-xs text-gray-400 text-right shrink-0">
              {{ r.divisions }} div · {{ r.teachers.toLocaleString() }} tchr
            </div>
          </div>
        </div>
      </div>

      <!-- ── Per-division table ──────────────────────────────────────── -->
      <div class="bg-white rounded-2xl shadow border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b bg-gray-50 flex flex-wrap items-center gap-3">
          <h2 class="font-bold text-[#1a4e8f] mr-auto">Division-Level Estimates</h2>
          <!-- Search -->
          <input
            v-model="divisionSearch"
            placeholder="Search division or region…"
            class="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#1a4e8f]/30 w-52"
          />
          <!-- Tier filter -->
          <select
            v-model="tierFilter"
            class="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#1a4e8f]/30"
          >
            <option>All</option>
            <option>Critical Priority</option>
            <option>High Priority</option>
            <option>Standard Priority</option>
          </select>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th class="px-4 py-3 text-left">Division</th>
                <th class="px-4 py-3 text-left">Region</th>
                <th class="px-4 py-3 text-left">Tier</th>
                <th class="px-4 py-3 text-left">Intervention</th>
                <th class="px-4 py-3 text-right">Teachers</th>
                <th class="px-4 py-3 text-right">Schools</th>
                <th class="px-4 py-3 text-right">Geo ×</th>
                <th class="px-4 py-3 text-right">Est. Cost</th>
                <th class="px-4 py-3 text-center">Details</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <template v-for="d in filteredDivisions" :key="d.division">
                <tr class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-3 font-medium text-gray-800">{{ d.division }}</td>
                  <td class="px-4 py-3 text-gray-500">{{ d.region }}</td>
                  <td class="px-4 py-3">
                    <span
                      :class="[
                        'text-xs font-semibold px-2 py-0.5 rounded-full',
                        d.priority_tier === 'Critical Priority' ? 'bg-red-100 text-red-700' :
                        d.priority_tier === 'High Priority'     ? 'bg-amber-100 text-amber-700' :
                                                                   'bg-green-100 text-green-700'
                      ]"
                    >
                      {{ d.priority_tier === 'Critical Priority' ? '🔴' : d.priority_tier === 'High Priority' ? '🟠' : '🟢' }}
                      {{ d.priority_tier.replace(' Priority', '') }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-gray-600 text-xs max-w-[180px] truncate" :title="d.intervention_label">
                    {{ d.intervention_label }}
                  </td>
                  <td class="px-4 py-3 text-right text-gray-700">{{ d.total_teachers.toLocaleString() }}</td>
                  <td class="px-4 py-3 text-right text-gray-700">{{ d.total_schools }}</td>
                  <td class="px-4 py-3 text-right text-xs font-mono"
                      :class="d.geo_multiplier >= 1.4 ? 'text-red-600 font-bold' : d.geo_multiplier >= 1.2 ? 'text-amber-600' : 'text-gray-400'">
                    {{ d.geo_multiplier.toFixed(2) }}×
                  </td>
                  <td class="px-4 py-3 text-right font-semibold text-[#1a4e8f]">{{ pesoShort(d.estimated_cost) }}</td>
                  <td class="px-4 py-3 text-center">
                    <button
                      @click="expandedDivision = expandedDivision === d.division ? null : d.division"
                      class="text-xs text-[#1a4e8f] hover:underline"
                    >
                      {{ expandedDivision === d.division ? 'Hide' : 'Expand' }}
                    </button>
                  </td>
                </tr>

                <!-- Expanded breakdown row -->
                <tr v-if="expandedDivision === d.division" class="bg-blue-50/40">
                  <td colspan="9" class="px-6 py-4">
                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Cost Breakdown — {{ d.division }}</div>
                    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
                      <div
                        v-for="key in Object.keys(BREAKDOWN_COLORS)"
                        :key="key"
                        class="bg-white rounded-xl p-3 border border-gray-100 shadow-sm"
                      >
                        <div class="flex items-center gap-1.5 mb-1">
                          <span :class="['w-2.5 h-2.5 rounded-full', BREAKDOWN_COLORS[key]]" />
                          <span class="text-xs text-gray-500">{{ BREAKDOWN_LABELS[key] }}</span>
                        </div>
                        <div class="font-bold text-gray-800">{{ peso(d.breakdown[key]) }}</div>
                        <div class="text-xs text-gray-400">
                          {{ ((d.breakdown[key] / d.estimated_cost) * 100).toFixed(1) }}% of total
                        </div>
                      </div>
                    </div>
                    <div class="mt-3 text-xs text-gray-400">
                      Geographic multiplier: <strong>{{ d.geo_multiplier.toFixed(3) }}×</strong>
                      (geo disadvantage score: {{ (d.geo_disadvantage * 100).toFixed(1) }}%)
                      · Total: <strong class="text-[#1a4e8f]">{{ peso(d.estimated_cost) }}</strong>
                    </div>
                  </td>
                </tr>
              </template>

              <tr v-if="filteredDivisions.length === 0">
                <td colspan="9" class="px-4 py-8 text-center text-gray-400 text-sm">No divisions match your filter.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-6 py-3 bg-gray-50 border-t text-xs text-gray-400">
          Showing {{ filteredDivisions.length }} of {{ data.divisions.length }} divisions
        </div>
      </div>

      <!-- Disclaimer -->
      <p class="text-xs text-gray-400 text-center pb-4">
        * All figures are estimates based on standardised cost models per intervention type and adjusted for geographic remoteness.
        Actual costs may vary based on procurement, vendor rates, and DOST-SEI budget guidelines.
      </p>

    </template>
  </div>
</template>
