/**
 * API composable — wraps $fetch calls to the FastAPI backend.
 * Local development uses Nuxt's /api proxy. Deployed builds set
 * NUXT_PUBLIC_API_BASE so SSR and client fetches target the Vercel API.
 */

import type {
  Division,
  Region,
  StatsOverview,
  PaginatedDivisions,
} from "~/types";

export const useApi = () => {
  const config = useRuntimeConfig();
  const apiBase = String(config.public.apiBase || "").replace(/\/+$/, "");
  const apiUrl = (path: string) =>
    `${apiBase}${path.startsWith("/") ? path : `/${path}`}`;
  const BASE = apiUrl("/api/v1");

  const stats = () => $fetch<StatsOverview>(`${BASE}/stats`);

  const topDivisions = (n = 15) =>
    $fetch<Division[]>(`${BASE}/divisions/top?n=${n}`);

  const divisions = (params?: {
    page?: number;
    page_size?: number;
    region?: string;
    tier?: string;
    search?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    if (params?.region) q.set("region", params.region);
    if (params?.tier) q.set("tier", params.tier);
    if (params?.search) q.set("search", params.search);
    return $fetch<PaginatedDivisions>(`${BASE}/divisions?${q.toString()}`);
  };

  const division = (name: string) =>
    $fetch<Division>(`${BASE}/divisions/${encodeURIComponent(name)}`);

  const regions = () => $fetch<Region[]>(`${BASE}/regions`);

  const regionDivisions = (name: string) =>
    $fetch<Division[]>(
      `${BASE}/regions/${encodeURIComponent(name)}/divisions`
    );

  return {
    apiUrl,
    stats,
    topDivisions,
    divisions,
    division,
    regions,
    regionDivisions,
  };
};
