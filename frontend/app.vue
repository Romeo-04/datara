<template>
  <div>
    <!-- Global Navigation -->
    <nav class="bg-[#1a4e8f] text-white px-6 py-3 flex items-center gap-4 shadow-md">
      <div class="flex items-center gap-2">
        <div
          class="w-8 h-8 bg-[#f5a623] rounded-full flex items-center justify-center font-bold text-[#1a4e8f] text-sm"
        >
          S
        </div>
        <div>
          <div class="font-bold text-sm leading-tight">
            STAR Regional Intelligence System
          </div>
          <div class="text-xs text-blue-200">
            DOST-SEI · Capacity-Building Decision Support
          </div>
        </div>
      </div>
      <div class="ml-auto flex gap-6 text-sm">
        <NuxtLink to="/" class="hover:text-[#f5a623] transition-colors">
          Dashboard
        </NuxtLink>
        <NuxtLink
          to="/divisions"
          class="hover:text-[#f5a623] transition-colors"
        >
          Divisions
        </NuxtLink>
        <NuxtLink to="/regions" class="hover:text-[#f5a623] transition-colors">
          Regions
        </NuxtLink>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="min-h-screen">
      <NuxtPage />
    </main>

    <!-- Footer -->
    <footer class="text-center text-xs text-gray-400 py-6 border-t mt-12">
      STAR Regional Intelligence System · START a Ton Challenge · DOST-SEI STAR
      Program
    </footer>
  </div>
</template>
