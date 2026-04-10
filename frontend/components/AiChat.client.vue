<script setup lang="ts">
interface Message {
  role: "user" | "assistant";
  text: string;
}

function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/_(.+?)_/g, "<em>$1</em>")
    .replace(/^• (.+)$/gm, "<li>$1</li>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul class='list-none space-y-0.5 mt-1'>$1</ul>")
    .replace(/\n{2,}/g, "</p><p class='mt-1'>")
    .replace(/\n/g, "<br/>")
}

const open = ref(false);
const input = ref("");
const loading = ref(false);
const messages = ref<Message[]>([
  {
    role: "assistant",
    text: "Hi! I'm STARSight AI. Ask me anything about the regions, divisions, UAI scores, or interventions shown in this dashboard.",
  },
]);

const messagesEl = ref<HTMLElement | null>(null);

async function send() {
  const text = input.value.trim();
  if (!text || loading.value) return;

  messages.value.push({ role: "user", text });
  input.value = "";
  loading.value = true;

  await nextTick();
  scrollToBottom();

  try {
    const res = await $fetch<{ reply: string }>("/api/v1/chat", {
      method: "POST",
      body: { message: text },
    });
    messages.value.push({ role: "assistant", text: res.reply });
  } catch {
    messages.value.push({
      role: "assistant",
      text: "Sorry, I couldn't connect to the AI. Make sure the backend is running.",
    });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}
</script>

<template>
  <!-- Floating button -->
  <button
    v-if="!open"
    @click="open = true"
    class="fixed bottom-6 right-6 z-[2000] w-14 h-14 rounded-full shadow-xl
           bg-[#1a4e8f] hover:bg-[#163f73] text-white flex items-center justify-center
           transition-all duration-200 hover:scale-105"
    title="Ask STARSight AI"
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3v-3z" />
    </svg>
  </button>

  <!-- Chat panel -->
  <div
    v-if="open"
    class="fixed bottom-6 right-6 z-[2000] w-[360px] max-h-[560px] flex flex-col
           bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden"
  >
    <!-- Header -->
    <div class="bg-[#1a4e8f] text-white px-4 py-3 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-full bg-[#f5a623] flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-[#1a4e8f]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <div class="font-semibold text-sm leading-tight">STARSight AI</div>
          <div class="text-xs text-blue-200">Ask about the dashboard data</div>
        </div>
      </div>
      <button @click="open = false" class="text-blue-200 hover:text-white transition-colors p-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Messages -->
    <div ref="messagesEl" class="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
      >
        <div
          :class="[
            'max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed',
            msg.role === 'user'
              ? 'bg-[#1a4e8f] text-white rounded-tr-sm whitespace-pre-wrap'
              : 'bg-gray-100 text-gray-800 rounded-tl-sm',
          ]"
          v-html="msg.role === 'assistant' ? renderMarkdown(msg.text) : msg.text"
        />
      </div>

      <!-- Typing indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-2.5 flex gap-1 items-center">
          <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0ms" />
          <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:150ms" />
          <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:300ms" />
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="px-3 pb-3 pt-2 border-t border-gray-100 shrink-0">
      <div class="flex gap-2 items-end">
        <textarea
          v-model="input"
          @keydown="onKeydown"
          placeholder="Ask about regions, divisions, UAI scores…"
          rows="2"
          class="flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2 text-sm
                 focus:outline-none focus:ring-2 focus:ring-[#1a4e8f]/30 focus:border-[#1a4e8f]
                 placeholder-gray-400"
        />
        <button
          @click="send"
          :disabled="!input.trim() || loading"
          class="w-9 h-9 rounded-xl bg-[#1a4e8f] text-white flex items-center justify-center
                 disabled:opacity-40 hover:bg-[#163f73] transition-colors shrink-0"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <div class="text-xs text-gray-400 mt-1.5 text-center">Enter to send · Shift+Enter for new line</div>
    </div>
  </div>
</template>
