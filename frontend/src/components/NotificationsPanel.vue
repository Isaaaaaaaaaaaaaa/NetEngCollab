<template>
  <!-- 该组件不渲染可见 UI，仅负责轮询后端并触发 Element Plus 的通知 -->
  <span style="display: none"></span>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";
import { ElNotification } from "element-plus";


const shown = ref<Set<number>>(new Set());


async function load() {
  try {
    try {
      await axios.post("/api/match/check");
    } catch {
    }
    const resp = await axios.get("/api/notifications", { params: { page: 1, page_size: 100 } });
    const unread = resp.data.items.filter((x: any) => !x.is_read);
    for (const n of unread) {
      if (shown.value.has(n.id)) continue;
      shown.value.add(n.id);
      ElNotification({
        title: n.title || "系统提醒",
        message: n.payload && n.payload.summary ? n.payload.summary : "",
        position: "top-right",
        duration: 5000,
        type: "info"
      });
    }
  } catch (e) {
    // ignore
  }
}


onMounted(() => {
  load();
  setInterval(load, 15000);
});
</script>
