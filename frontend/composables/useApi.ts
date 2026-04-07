/**
 * API composable — wraps $fetch calls to the FastAPI backend.
 * Nuxt's nitro proxy forwards /api/** → http://localhost:8000/api/**
 * so both SSR and client-side fetches use the same relative paths.
 */

import type {
  Division,
  Region,
  StatsOverview,
  PaginatedDivisions,
} from "~/types";

export const useApi = () => {
  const BASE = "/api/v1";

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

  return { stats, topDivisions, divisions, division, regions, regionDivisions };
};
