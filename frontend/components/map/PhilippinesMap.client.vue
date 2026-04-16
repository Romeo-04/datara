<script setup lang="ts">
import type { Region, Division } from "~/types";

const props = defineProps<{
  regions: Region[];
  divisions: Division[];
}>();

const mapEl = ref<HTMLElement | null>(null);

// Backend region name → PSGC code (matches faeldon/philippines-json-maps 2023 lowres filenames)
const REGION_PSGC: Record<string, string> = {
  "NCR":          "1300000000",
  "CAR":          "1400000000",
  "Region I":     "100000000",
  "Region II":    "200000000",
  "Region III":   "300000000",
  "Region IV-A":  "400000000",
  "Region IV-B":  "1700000000",
  "Region V":     "500000000",
  "Region VI":    "600000000",
  "Region VII":   "700000000",
  "Region VIII":  "800000000",
  "Region IX":    "900000000",
  "Region X":     "1000000000",
  "Region XI":    "1100000000",
  "Region XII":   "1200000000",
  "Region XIII":  "1600000000",
  "BARMM":        "1900000000",
};

const GEOJSON_BASE = "https://raw.githubusercontent.com/faeldon/philippines-json-maps/master/2023/geojson/regions/lowres";

// Label anchor points (center of each region for label placement)
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

function uaiToColor(uai: number): string {
  if (uai >= 0.65) return "#c0392b";
  if (uai >= 0.40) return "#e67e22";
  return "#27ae60";
}

function uaiBorderColor(uai: number): string {
  if (uai >= 0.65) return "#922b21";
  if (uai >= 0.40) return "#9a6412";
  return "#1e8449";
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

  // Build a lookup map from region name → region data
  const regionByName: Record<string, any> = {};
  props.regions.forEach((r: any) => { regionByName[r.region] = r; });

  // Fetch all region GeoJSON files in parallel
  const regionEntries = Object.entries(REGION_PSGC);
  const geoResults = await Promise.allSettled(
    regionEntries.map(([, psgc]) =>
      fetch(`${GEOJSON_BASE}/provdists-region-${psgc}.0.001.json`).then(r => r.json())
    )
  );

  geoResults.forEach((result, i) => {
    const [regionName] = regionEntries[i];
    if (result.status !== "fulfilled") return;

    const geoData = result.value;
    const region = regionByName[regionName];
    if (!region) return;

    const uai = parseFloat(region.avg_uai_score ?? 0);
    const color  = uaiToColor(uai);
    const border = uaiBorderColor(uai);
    const critical = region.critical_divisions ?? 0;
    const high     = region.high_divisions ?? 0;

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
          <span style="font-weight:600">${Number(region.total_teachers).toLocaleString()}</span>
          <span style="color:#666">Mismatch Rate</span>
          <span style="font-weight:600">${(parseFloat(region.avg_mismatch_rate) * 100).toFixed(1)}%</span>
          <span style="color:#666">NAT MPS</span>
          <span style="font-weight:600">${parseFloat(region.avg_nat_combined_mps).toFixed(1)}%</span>
        </div>
        <a href="/regions/${encodeURIComponent(region.region)}"
           style="display:block;margin-top:8px;text-align:center;color:#1a4e8f;font-size:12px;
                  font-weight:600;text-decoration:none;border:1px solid #1a4e8f;border-radius:4px;padding:3px 0">
          View Region Detail →
        </a>
      </div>`;

    const geoLayer = L.geoJSON(geoData, {
      style: {
        fillColor:   color,
        color:       border,
        weight:      1.2,
        opacity:     0.9,
        fillOpacity: 0.35,
      },
      onEachFeature: (_feature, layer) => {
        layer.bindPopup(popupHtml, { maxWidth: 250 });
        layer.on("mouseover", function (this: any) {
          this.setStyle({ fillOpacity: 0.6, weight: 2 });
        });
        layer.on("mouseout", function (this: any) {
          geoLayer.resetStyle(this);
        });
      },
    }).addTo(map);

    // Region label
    const center = REGION_CENTERS[regionName];
    if (center) {
      L.marker(center, {
        icon: L.divIcon({
          className: "",
          html: `<div style="display:inline-block;font-size:9px;font-weight:800;color:#1a4e8f;
                              background:rgba(255,255,255,0.88);padding:2px 6px;border-radius:4px;
                              white-space:nowrap;pointer-events:none;
                              transform:translate(-50%,-50%);box-shadow:0 1px 3px rgba(0,0,0,0.18)">
                   ${regionName}
                 </div>`,
          iconSize: [0, 0],
          iconAnchor: [0, 0],
        }),
      }).addTo(map);
    }
  });

  // Actual geographic coordinates for each division
  const DIVISION_COORDS: Record<string, [number, number]> = {
    // BARMM
    "Basilan":              [6.6825, 122.0676],
    "Lanao del Sur":        [7.8231, 124.4357],
    "Maguindanao":          [6.9414, 124.4146],
    "Sulu":                 [6.0474, 121.0038],
    "Tawi-Tawi":            [5.1339, 119.9536],
    // CAR
    "Abra":                 [17.5980, 120.4553],
    "Apayao":               [18.0124, 121.1454],
    "Benguet":              [16.4023, 120.5960],
    "Ifugao":               [16.8333, 121.1753],
    "Kalinga":              [17.4720, 121.3592],
    "Mountain Province":    [17.0490, 120.9866],
    // NCR
    "Caloocan":             [14.6515, 120.9670],
    "Manila":               [14.5995, 120.9842],
    "Pasig":                [14.5764, 121.0851],
    "Quezon City":          [14.6760, 121.0437],
    "Taguig":               [14.5176, 121.0509],
    // Region I
    "Ilocos Norte":         [18.1647, 120.7116],
    "Ilocos Sur":           [17.5761, 120.3869],
    "La Union":             [16.6152, 120.3190],
    "Pangasinan":           [15.8949, 120.2863],
    // Region II
    "Batanes":              [20.4487, 121.9702],
    "Cagayan":              [17.6132, 121.7270],
    "Isabela":              [16.9754, 121.8107],
    "Nueva Vizcaya":        [16.3301, 121.1710],
    "Quirino":              [16.4907, 121.5402],
    // Region III
    "Aurora":               [15.9784, 121.6459],
    "Bataan":               [14.6417, 120.4818],
    "Bulacan":              [14.7942, 120.8799],
    "Nueva Ecija":          [15.5783, 121.0690],
    "Pampanga":             [15.0794, 120.6200],
    "Tarlac":               [15.4755, 120.5960],
    "Zambales":             [15.5082, 120.0697],
    // Region IV-A
    "Batangas":             [13.7565, 121.0583],
    "Cavite":               [14.2456, 120.8787],
    "Laguna":               [14.2691, 121.4113],
    "Quezon":               [14.0313, 122.1101],
    "Rizal":                [14.6037, 121.3084],
    // Region IV-B
    "Marinduque":           [13.4767, 121.9032],
    "Occidental Mindoro":   [12.9577, 120.6200],
    "Oriental Mindoro":     [13.0565, 121.4069],
    "Palawan":              [9.8349,  118.7384],
    "Romblon":              [12.5778, 122.2695],
    // Region V
    "Albay":                [13.1775, 123.5280],
    "Camarines Norte":      [14.1390, 122.7632],
    "Camarines Sur":        [13.6252, 123.1853],
    "Catanduanes":          [13.7089, 124.2422],
    "Masbate":              [12.3696, 123.6217],
    "Sorsogon":             [12.9433, 123.9447],
    // Region VI
    "Aklan":                [11.8166, 122.0942],
    "Antique":              [11.3650, 122.0965],
    "Capiz":                [11.5525, 122.7411],
    "Guimaras":             [10.5954, 122.6277],
    "Iloilo":               [10.7202, 122.5621],
    "Negros Occidental":    [10.6713, 123.0036],
    // Region VII
    "Bohol":                [9.8468,  124.1435],
    "Cebu":                 [10.3157, 123.8854],
    "Negros Oriental":      [9.6168,  123.0115],
    "Siquijor":             [9.2045,  123.5226],
    // Region VIII
    "Biliran":              [11.5830, 124.4619],
    "Eastern Samar":        [11.6508, 125.4082],
    "Leyte":                [10.8731, 124.8811],
    "Northern Samar":       [12.5271, 124.6460],
    "Samar":                [11.7490, 125.0285],
    "Southern Leyte":       [10.3346, 125.1719],
    // Region IX
    "Zamboanga Sibugay":    [7.5222,  122.8198],
    "Zamboanga del Norte":  [8.1527,  123.2577],
    "Zamboanga del Sur":    [7.8383,  123.2968],
    // Region X
    "Bukidnon":             [8.0515,  125.0987],
    "Camiguin":             [9.1730,  124.7300],
    "Lanao del Norte":      [8.0730,  124.2873],
    "Misamis Occidental":   [8.3375,  123.7071],
    "Misamis Oriental":     [8.5046,  124.6219],
    // Region XI
    "Davao Occidental":     [6.1040,  125.6133],
    "Davao Oriental":       [7.3172,  126.5420],
    "Davao de Oro":         [7.3172,  126.1731],
    "Davao del Norte":      [7.5619,  125.8039],
    "Davao del Sur":        [6.7659,  125.3284],
    // Region XII
    "Cotabato":             [7.2047,  124.2310],
    "Sarangani":            [5.9234,  125.1929],
    "South Cotabato":       [6.3373,  124.7741],
    "Sultan Kudarat":       [6.5069,  124.4200],
    // Region XIII
    "Agusan del Norte":     [8.9461,  125.5320],
    "Agusan del Sur":       [8.1629,  126.0141],
    "Dinagat Islands":      [10.1284, 125.6012],
    "Surigao del Norte":    [9.7851,  125.4957],
    "Surigao del Sur":      [8.7513,  126.1367],
  };

  // Division dots — visible only at zoom >= 8
  const divisionLayer = L.layerGroup();

  props.divisions.forEach((div) => {
    const coords = DIVISION_COORDS[div.division];
    if (!coords) return;

    const [lat, lng] = coords;
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
        <span class="w-4 h-4 rounded-sm bg-red-600 inline-block border border-red-800" />
        Critical Priority (≥ 0.65)
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-sm bg-orange-500 inline-block border border-orange-700" />
        High Priority (0.40 – 0.65)
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-sm bg-green-500 inline-block border border-green-700" />
        Standard Priority (&lt; 0.40)
      </div>
      <div class="pt-1 border-t text-gray-400">Click a region to see details</div>
      <div class="text-gray-400">Zoom in (level 8+) for division dots</div>
    </div>
  </div>
</template>
