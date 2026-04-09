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
  "Region IV-B": [10.5000, 119.5000],
  "Region V":    [13.4208, 123.4136],
  "Region VI":   [11.0000, 122.6000],
  "Region VII":  [10.0000, 124.0000],
  "Region VIII": [11.5000, 125.0000],
  "Region IX":   [7.8000,  123.4000],
  "Region X":    [8.1000,  124.8000],
  "Region XI":   [7.1000,  125.8000],
  "Region XII":  [6.5000,  124.8000],
  "Region XIII": [8.9456,  125.9000],
  "BARMM":       [6.9000,  124.2000],
};

// Real-world radii (meters) to approximate each region's land mass
const REGION_RADII: Record<string, number> = {
  "NCR":         22000,
  "CAR":         95000,
  "Region I":    85000,
  "Region II":   110000,
  "Region III":  90000,
  "Region IV-A": 88000,
  "Region IV-B": 150000,
  "Region V":    105000,
  "Region VI":   95000,
  "Region VII":  80000,
  "Region VIII": 115000,
  "Region IX":   85000,
  "Region X":    95000,
  "Region XI":   85000,
  "Region XII":  95000,
  "Region XIII": 105000,
  "BARMM":       130000,
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
  await nextTick();
  if (!mapEl.value) return;

  const [leafletModule] = await Promise.all([
    import("leaflet"),
    import("leaflet/dist/leaflet.css"),
  ]);
  const L = leafletModule.default;

  const map = L.map(mapEl.value, { zoomControl: true }).setView([11.5, 122.5], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
    maxZoom: 16,
  }).addTo(map);

  setTimeout(() => map.invalidateSize(), 100);

  // Region coverage circles — L.circle uses real-world meters so they scale with zoom
  props.regions.forEach((region: any) => {
    const center = REGION_CENTERS[region.region];
    if (!center) return;

    const uai = region.avg_uai_score ?? 0.3;
    const color = uaiToColor(uai);
    const radius = REGION_RADII[region.region] ?? 90000;
    const critical = region.critical_divisions ?? 0;
    const high = region.high_divisions ?? 0;

    const popupHtml = `
      <div style="min-width:210px;font-family:system-ui,sans-serif">
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
      </div>`;

    // Large translucent fill — covers land mass
    L.circle(center, {
      radius,
      fillColor: color,
      color: color,
      weight: 2,
      opacity: 0.7,
      fillOpacity: 0.22,
      interactive: false,
    }).addTo(map);

    // Solid center dot for click/label — always visible
    L.circleMarker(center, {
      radius: 10,
      fillColor: color,
      color: "#fff",
      weight: 2.5,
      opacity: 1,
      fillOpacity: 1,
    })
      .bindPopup(popupHtml, { maxWidth: 250 })
      .addTo(map);

    // Region label
    L.marker(center, {
      icon: L.divIcon({
        className: "",
        html: `<div style="font-size:9px;font-weight:800;color:#1a4e8f;text-align:center;
                            background:rgba(255,255,255,0.75);padding:1px 4px;border-radius:3px;
                            white-space:nowrap;pointer-events:none;margin-top:14px">
                 ${region.region}
               </div>`,
        iconAnchor: [30, -2],
      }),
    }).addTo(map);
  });

  // Division dots — visible only at zoom >= 8
  const divisionLayer = L.layerGroup();

  props.divisions.forEach((div) => {
    const regionCenter = REGION_CENTERS[div.region];
    if (!regionCenter) return;

    const hash = div.division.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
    const lat = regionCenter[0] + ((hash % 17) - 8) * 0.12;
    const lng = regionCenter[1] + ((hash % 13) - 6) * 0.12;
    const color = uaiToColor(div.uai_score);

    L.circleMarker([lat, lng], {
      radius: 7,
      fillColor: color,
      color: "#fff",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.9,
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
  <div class="relative" style="width:100%;height:calc(100vh - 56px)">
    <div ref="mapEl" style="width:100%;height:100%" />

    <!-- Legend -->
    <div class="absolute bottom-8 left-4 z-[1000] bg-white border border-gray-200 rounded-xl shadow-md p-3 text-xs space-y-1.5">
      <div class="font-semibold text-gray-700 mb-2">UAI Priority Level</div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-red-600 inline-block border-2 border-white shadow" />
        Critical Priority (≥ 0.65)
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-orange-500 inline-block border-2 border-white shadow" />
        High Priority (0.40 – 0.65)
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-green-500 inline-block border-2 border-white shadow" />
        Standard Priority (&lt; 0.40)
      </div>
      <div class="pt-1 border-t text-gray-400">Shaded area = region coverage</div>
      <div class="text-gray-400">Zoom in (level 8+) for division dots</div>
    </div>
  </div>
</template>
