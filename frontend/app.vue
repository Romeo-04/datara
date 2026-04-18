<template>
  <div>
    <!-- Global Navigation -->
    <nav class="bg-[#1a4e8f] text-white px-6 py-3 flex items-center gap-4 shadow-md">
      <NuxtLink to="/" class="flex items-center">
        <img src="/text_logo.png" alt="STARSight" class="h-9 w-auto" style="filter:brightness(0) invert(1)" />
      </NuxtLink>
      <div class="ml-auto flex gap-6 text-sm">
        <NuxtLink to="/" class="hover:text-[#f5a623] transition-colors">
          Dashboard
        </NuxtLink>
        <NuxtLink to="/map" class="hover:text-[#f5a623] transition-colors">
          Map
        </NuxtLink>
        <NuxtLink to="/divisions" class="hover:text-[#f5a623] transition-colors">
          Divisions
        </NuxtLink>
        <NuxtLink to="/regions" class="hover:text-[#f5a623] transition-colors">
          Regions
        </NuxtLink>
        <NuxtLink to="/budget" class="hover:text-[#f5a623] transition-colors">
          Budget
        </NuxtLink>
        <NuxtLink
          to="/upload"
          class="bg-[#f5a623] text-[#1a4e8f] font-semibold px-3 py-0.5 rounded-lg hover:bg-yellow-400 transition-colors"
        >
          Upload Data
        </NuxtLink>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="min-h-screen">
      <NuxtPage />
    </main>

    <!-- Footer -->
    <footer class="text-center text-xs text-gray-400 py-6 border-t mt-12">
      STARSight · START a Ton Challenge · DOST-SEI STAR Program
    </footer>

    <!-- AI Chat Widget -->
    <AiChat />
  </div>
</template>
