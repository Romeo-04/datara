<script setup lang="ts">
import type { Region, Division } from "~/types";

const props = defineProps<{
  regions: Region[];
  divisions: Division[];
}>();

const mapEl = ref<HTMLElement | null>(null);

const REGION_CENTERS: Record<string, [number, number]> = {
  "NCR":         [14.5995, 120.9842],
  "CAR":         [17.3521, 121.1736],
  "Region I":    [15.8949, 120.2863],
  "Region II":   [17.6132, 121.7270],
  "Region III":  [15.4827, 120.7120],
  "Region IV-A": [14.1007, 121.0794],
  "Region IV-B": [11.1784, 121.6063],
  "Region V":    [13.4208, 123.4136],
  "Region VI":   [11.0000, 122.5000],
  "Region VII":  [10.3157, 123.8854],
  "Region VIII": [11.2440, 124.9762],
  "Region IX":   [8.1521,  123.2655],
  "Region X":    [8.0022,  124.6484],
  "Region XI":   [7.3041,  126.0893],
  "Region XII":  [6.2969,  124.6859],
  "Region XIII": [8.9456,  125.5438],
  "BARMM":       [7.0083,  124.2421],
};

function uaiToColor(uai: number): string {
  if (uai >= 0.65) return "#c0392b";
  if (uai >= 0.40) return "#e67e22";
  return "#27ae60";
}

function uaiToLabel(uai: number): string {
  if (uai >= 0.65) return "Critical Priority";
  if (uai >= 0.40) return "High Priority";
  return "Standard Priority";
}

onMounted(async () => {
  if (!mapEl.value) return;

  const L = (await import("leaflet")).default;
  await import("leaflet/dist/leaflet.css");

  const map = L.map(mapEl.value, { zoomControl: true }).setView([12.0, 122.5], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
    maxZoom: 13,
  }).addTo(map);

  // Region circles
  props.regions.forEach((region: any) => {
    const center = REGION_CENTERS[region.region];
    if (!center) return;

    const uai = region.avg_uai_score ?? 0.3;
    const color = uaiToColor(uai);
    const radius = Math.min(Math.max(18 + (region.total_teachers / 800) * 10, 16), 38);

    const circle = L.circleMarker(center, {
      radius,
      fillColor: color,
      color: "#fff",
      weight: 2.5,
      opacity: 1,
      fillOpacity: 0.85,
    }).addTo(map);

    const critical = region.critical_divisions ?? 0;
    const high = region.high_divisions ?? 0;

    circle.bindPopup(`
      <div style="min-width:200px;font-family:system-ui,sans-serif">
        <div style="font-weight:700;font-size:14px;margin-bottom:6px;color:#1a4e8f">${region.region}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:12px">
          <span style="color:#666">Avg UAI Score</span>
          <span style="font-weight:600;color:${color}">${uai.toFixed(3)}</span>
          <span style="color:#666">Priority</span>
          <span style="font-weight:600;color:${color}">${uaiToLabel(uai)}</span>
          <span style="color:#666">Divisions</span>
          <span style="font-weight:600">${region.n_divisions}</span>
          <span style="color:#666">Critical</span>
          <span style="font-weight:600;color:#c0392b">${critical}</span>
          <span style="color:#666">High Priority</span>
          <span style="font-weight:600;color:#e67e22">${high}</span>
          <span style="color:#666">Teachers</span>
          <span style="font-weight:600">${region.total_teachers.toLocaleString()}</span>
          <span style="color:#666">Mismatch Rate</span>
          <span style="font-weight:600">${(region.avg_mismatch_rate * 100).toFixed(1)}%</span>
          <span style="color:#666">NAT MPS</span>
          <span style="font-weight:600">${region.avg_nat_combined_mps.toFixed(1)}%</span>
        </div>
        <a href="/regions/${encodeURIComponent(region.region)}"
           style="display:block;margin-top:8px;text-align:center;color:#1a4e8f;font-size:12px;
                  font-weight:600;text-decoration:none;border:1px solid #1a4e8f;border-radius:4px;padding:3px 0">
          View Region Detail →
        </a>
      </div>`, { maxWidth: 240 }
    );

    // Region label
    L.marker(center, {
      icon: L.divIcon({
        className: "",
        html: `<div style="font-size:9px;font-weight:700;color:white;text-align:center;
                            text-shadow:0 1px 2px rgba(0,0,0,0.8);white-space:nowrap;
                            pointer-events:none">${region.region}</div>`,
        iconAnchor: [30, -14],
      }),
    }).addTo(map);
  });

  // Division dots — visible only at zoom >= 8
  const divisionLayer = L.layerGroup();

  props.divisions.forEach((div) => {
    const regionCenter = REGION_CENTERS[div.region];
    if (!regionCenter) return;

    // Deterministic jitter so dots spread around region center
    const hash = div.division.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
    const lat = regionCenter[0] + ((hash % 17) - 8) * 0.12;
    const lng = regionCenter[1] + ((hash % 13) - 6) * 0.12;
    const color = uaiToColor(div.uai_score);

    L.circleMarker([lat, lng], {
      radius: 6,
      fillColor: color,
      color: "#fff",
      weight: 1,
      opacity: 0.9,
      fillOpacity: 0.75,
    })
      .bindPopup(`
        <div style="font-family:system-ui,sans-serif;min-width:160px">
          <div style="font-weight:700;font-size:13px;color:#1a4e8f;margin-bottom:4px">${div.division}</div>
          <div style="font-size:11px;color:#666;margin-bottom:4px">${div.region}</div>
          <div style="font-size:12px"><b>UAI:</b> ${div.uai_score.toFixed(3)} &nbsp; <b>Rank:</b> #${div.priority_rank}</div>
          <div style="font-size:12px"><b>Tier:</b> <span style="color:${color}">${div.priority_tier}</span></div>
          <a href="/divisions/${encodeURIComponent(div.division)}"
             style="display:block;margin-top:6px;text-align:center;color:#1a4e8f;font-size:11px;
                    font-weight:600;text-decoration:none;border:1px solid #1a4e8f;border-radius:4px;padding:2px 0">
            View Detail →
          </a>
        </div>`)
      .addTo(divisionLayer);
  });

  map.on("zoomend", () => {
    if (map.getZoom() >= 8) {
      divisionLayer.addTo(map);
    } else {
      map.removeLayer(divisionLayer);
    }
  });
});
</script>

<template>
  <div class="relative w-full h-full">
    <div ref="mapEl" class="w-full h-full rounded-xl z-0" />

    <!-- Legend -->
    <div class="absolute bottom-8 left-4 z-[1000] bg-white border border-gray-200 rounded-xl shadow-md p-3 text-xs space-y-1.5">
      <div class="font-semibold text-gray-700 mb-2">UAI Priority Level</div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-red-500 inline-block border-2 border-white shadow" />
        Critical Priority (≥ 0.65)
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-amber-500 inline-block border-2 border-white shadow" />
        High Priority (0.40 – 0.65)
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-green-500 inline-block border-2 border-white shadow" />
        Standard Priority (&lt; 0.40)
      </div>
      <div class="pt-1 border-t text-gray-400">Circle size = teacher count</div>
      <div class="text-gray-400">Zoom in (level 8+) for division dots</div>
    </div>
  </div>
</template>
