<script setup lang="ts">
const { apiUrl } = useApi();

const { data: schema } = await useAsyncData("upload-schema", () =>
  $fetch<{ files: any[] }>(apiUrl("/api/v1/upload/schema"))
);

interface FileSlot {
  key: string;
  label: string;
  required_columns: string[];
  all_columns: string[];
  optional: boolean;
  file: File | null;
  dragOver: boolean;
}

const slots = ref<FileSlot[]>(
  (schema.value?.files ?? []).map((f: any) => ({ ...f, file: null, dragOver: false }))
);

const uploading = ref(false);
const result = ref<any>(null);
const error = ref<string | null>(null);

function onFileSelect(key: string, event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] ?? null;
  setFile(key, file);
}

function onDrop(key: string, event: DragEvent) {
  event.preventDefault();
  const slot = slots.value.find((s) => s.key === key);
  if (slot) slot.dragOver = false;
  const file = event.dataTransfer?.files?.[0] ?? null;
  if (file?.name.endsWith(".csv")) setFile(key, file);
}

function setFile(key: string, file: File | null) {
  const slot = slots.value.find((s) => s.key === key);
  if (slot) slot.file = file;
  result.value = null;
  error.value = null;
}

async function submitUpload() {
  if (!slots.value.some((s) => s.file)) {
    error.value = "Please select at least one CSV file before uploading.";
    return;
  }
  uploading.value = true;
  error.value = null;
  result.value = null;

  try {
    const formData = new FormData();
    slots.value.forEach((s) => { if (s.file) formData.append(s.key, s.file); });
    result.value = await $fetch<any>(apiUrl("/api/v1/upload"), { method: "POST", body: formData });
    slots.value.forEach((s) => (s.file = null));
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? "Upload failed.";
  } finally {
    uploading.value = false;
  }
}

const anyFileSelected = computed(() => slots.value.some((s) => s.file !== null));
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Upload Dataset</h1>
      <p class="text-sm text-gray-500 mt-1">
        Upload your own CSV files to replace the current dataset.
        The system re-runs the full analysis pipeline and refreshes all rankings automatically.
      </p>
    </div>

    <!-- Info banner -->
    <div class="bg-blue-50 border border-blue-200 rounded-xl px-5 py-4 text-sm text-blue-800 flex gap-3">
      <span class="text-lg mt-0.5">ℹ</span>
      <div>
        <strong>How this works:</strong> Upload any combination of the four CSV files below.
        Files you don't upload fall back to the existing dataset.
        After upload, the pipeline re-runs instantly and all dashboard data is refreshed.
      </div>
    </div>

    <!-- File upload grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="slot in slots" :key="slot.key" class="card p-5 flex flex-col gap-3">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <div class="font-semibold text-gray-800 flex items-center gap-2">
              {{ slot.label }}
              <span v-if="slot.optional" class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Optional</span>
              <span v-else class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Required</span>
            </div>
            <div class="text-xs text-gray-400 mt-0.5">{{ slot.key }}.csv</div>
          </div>
          <div v-if="slot.file" class="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-sm font-bold">✓</div>
        </div>

        <!-- Drop zone -->
        <label
          :for="`file-${slot.key}`"
          :class="`block border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${
            slot.dragOver ? 'border-[#1a4e8f] bg-blue-50'
            : slot.file   ? 'border-green-400 bg-green-50'
                          : 'border-gray-300 hover:border-[#1a4e8f] hover:bg-gray-50'
          }`"
          @dragover.prevent="slot.dragOver = true"
          @dragleave="slot.dragOver = false"
          @drop="onDrop(slot.key, $event)"
        >
          <input :id="`file-${slot.key}`" type="file" accept=".csv" class="hidden" @change="onFileSelect(slot.key, $event)" />
          <div v-if="slot.file" class="space-y-1">
            <div class="text-sm font-medium text-green-700">{{ slot.file.name }}</div>
            <div class="text-xs text-gray-400">{{ (slot.file.size / 1024).toFixed(1) }} KB</div>
            <button type="button" class="text-xs text-red-500 hover:underline" @click.prevent="setFile(slot.key, null)">Remove</button>
          </div>
          <div v-else class="space-y-1">
            <div class="text-2xl text-gray-300">📄</div>
            <div class="text-sm text-gray-500">Drop CSV here or <span class="text-[#1a4e8f] font-medium">browse</span></div>
          </div>
        </label>

        <!-- Required columns -->
        <details class="text-xs text-gray-500">
          <summary class="cursor-pointer hover:text-gray-700 font-medium">Required columns ({{ slot.required_columns.length }})</summary>
          <div class="mt-2 flex flex-wrap gap-1">
            <span v-for="col in slot.required_columns" :key="col" class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono">{{ col }}</span>
          </div>
        </details>

        <!-- All columns -->
        <details class="text-xs text-gray-500">
          <summary class="cursor-pointer hover:text-gray-700 font-medium">All columns ({{ slot.all_columns.length }})</summary>
          <div class="mt-2 flex flex-wrap gap-1">
            <span v-for="col in slot.all_columns" :key="col" class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono">{{ col }}</span>
          </div>
        </details>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-sm text-red-700 flex gap-3">
      <span>✗</span><span>{{ error }}</span>
    </div>

    <!-- Success -->
    <div v-if="result" class="bg-green-50 border border-green-200 rounded-xl p-5 space-y-4">
      <div class="flex items-center gap-2 text-green-700 font-semibold">
        <span class="text-xl">✓</span>
        Upload successful — pipeline re-ran and data has been refreshed
      </div>

      <div>
        <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Files Processed</div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="(info, name) in result.uploaded_files" :key="name"
               class="bg-white border border-green-200 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-gray-900">{{ info.rows.toLocaleString() }}</div>
            <div class="text-xs text-gray-500">{{ String(name).replace("_", " ") }} rows</div>
          </div>
        </div>
      </div>

      <div v-if="result.pipeline_summary">
        <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Pipeline Results</div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-white border border-green-200 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-gray-800">{{ result.pipeline_summary.divisions }}</div>
            <div class="text-xs text-gray-500">Divisions Scored</div>
          </div>
          <div class="bg-white border border-green-200 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-gray-800">{{ result.pipeline_summary.regions }}</div>
            <div class="text-xs text-gray-500">Regions</div>
          </div>
          <div class="bg-white border border-red-200 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-red-600">{{ result.pipeline_summary.critical_divisions }}</div>
            <div class="text-xs text-gray-500">Critical Divisions</div>
          </div>
          <div class="bg-white border border-green-200 rounded-lg p-3 text-center">
            <div class="text-lg font-bold text-gray-800">{{ (result.pipeline_summary.mismatch_rate * 100).toFixed(1) }}%</div>
            <div class="text-xs text-gray-500">Mismatch Rate</div>
          </div>
        </div>
      </div>

      <div class="flex gap-3 pt-1">
        <NuxtLink to="/" class="bg-[#1a4e8f] text-white text-sm px-5 py-2 rounded-lg hover:bg-blue-800 transition-colors">
          View Updated Dashboard →
        </NuxtLink>
        <NuxtLink to="/map" class="border border-[#1a4e8f] text-[#1a4e8f] text-sm px-5 py-2 rounded-lg hover:bg-blue-50 transition-colors">
          View Map →
        </NuxtLink>
      </div>
    </div>

    <!-- Submit -->
    <div class="flex items-center gap-4">
      <button
        :disabled="!anyFileSelected || uploading"
        :class="`px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
          anyFileSelected && !uploading
            ? 'bg-[#1a4e8f] text-white hover:bg-blue-800'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`"
        @click="submitUpload"
      >
        <span v-if="uploading" class="flex items-center gap-2">
          <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          Running pipeline…
        </span>
        <span v-else>Upload & Run Analysis</span>
      </button>
      <span class="text-sm text-gray-400">
        {{ slots.filter((s) => s.file).length }} of {{ slots.length }} files selected
      </span>
    </div>

    <p class="text-xs text-gray-400 border-t pt-4">
      Uploaded files are processed server-side only. Individual teacher records are never stored
      in the dashboard outputs — all results are aggregated to division level before display.
    </p>
  </div>
</template>
