<template>
  <el-popover placement="bottom" :width="360" trigger="click">
    <template #reference>
      <el-badge :value="unread" :hidden="unread <= 0" :max="99">
        <el-button text size="small">消息</el-button>
      </el-badge>
    </template>

    <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:8px;">
      <div style="font-size:13px; font-weight:600;">消息提醒</div>
      <el-button size="small" text type="primary" :disabled="!unread" @click="markAllRead">全部已读</el-button>
    </div>

    <el-empty v-if="!items.length" description="暂无消息" />
    <div v-else class="bell-body">
      <div class="bell-scroll">
        <ul class="bell-list">
          <li v-for="n in items" :key="n.id" class="bell-item" @click="open(n)">
            <div class="bell-item-top">
              <span class="truncate bell-title">{{ n.title || '系统提醒' }}</span>
              <span v-if="!n.is_read" class="pill badge-amber bell-badge">未读</span>
            </div>
            <div v-if="n.payload?.summary" class="truncate bell-summary">
              {{ n.payload.summary }}
            </div>
            <div class="bell-time">{{ (n.created_at || '').slice(0, 16).replace('T', ' ') }}</div>
          </li>
        </ul>
      </div>
      <div v-if="hasMore" class="bell-more">
        <el-button size="small" text type="primary" :disabled="loadingMore" @click="loadMore">
          {{ loadingMore ? '加载中…' : '加载更多' }}
        </el-button>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import { useAuthStore } from "../store/auth";


const auth = useAuthStore();
const router = useRouter();

const items = ref<any[]>([]);
const timer = ref<number | null>(null);
const page = ref(1);
const pageSize = 30;
const hasMore = ref(false);
const loadingMore = ref(false);

const unread = computed(() => (items.value || []).filter(x => !x.is_read).length);


async function load() {
  try {
    await axios.post("/api/match/check");
  } catch {
  }
  try {
    page.value = 1;
    const resp = await axios.get("/api/notifications", { params: { page: page.value, page_size: pageSize } });
    items.value = resp.data.items || [];
    hasMore.value = !!resp.data.has_more;
  } catch {
    items.value = [];
    hasMore.value = false;
  }
}


async function loadMore() {
  if (!hasMore.value || loadingMore.value) return;
  loadingMore.value = true;
  try {
    const next = page.value + 1;
    const resp = await axios.get("/api/notifications", { params: { page: next, page_size: pageSize } });
    const more = resp.data.items || [];
    page.value = next;
    items.value = [...items.value, ...more];
    hasMore.value = !!resp.data.has_more;
  } catch {
  } finally {
    loadingMore.value = false;
  }
}


async function markRead(id: number) {
  try {
    await axios.post(`/api/notifications/${id}/read`);
  } catch {
  }
}


async function markAllRead() {
  const unreadItems = (items.value || []).filter(x => !x.is_read);
  for (const n of unreadItems) {
    await markRead(n.id);
  }
  await load();
}


function toRoleRoute(suffix: string) {
  const role = auth.user?.role;
  if (role === "student") return `student-${suffix}`;
  if (role === "teacher") return `teacher-${suffix}`;
  if (role === "admin") return `admin-${suffix}`;
  return null;
}


async function open(n: any) {
  if (!n) return;
  if (!n.is_read) {
    await markRead(n.id);
    n.is_read = true;
  }

  const t = n.notif_type;
  const p = n.payload || {};

  if (t === "message_new") {
    const name = toRoleRoute("messages");
    if (name) {
      await router.push({ name, query: p.conversation_id ? { conversation_id: String(p.conversation_id) } : undefined });
    }
    return;
  }

  if (t === "match_refresh") {
    const name = auth.user?.role === "student" ? "student-projects" : auth.user?.role === "teacher" ? "teacher-students" : null;
    if (name) await router.push({ name });
    return;
  }

  if (t.startsWith("cooperation_")) {
    const name = auth.user?.role === "student" ? "student-cooperation" : auth.user?.role === "teacher" ? "teacher-projects" : "admin-projects";
    await router.push({ name });
    return;
  }

  if (t === "forum_reply") {
    const name = toRoleRoute("forum");
    if (name) await router.push({ name });
    return;
  }

  if (t === "comment_reply" || t === "comment_new") {
    const targetType = p.target_type;
    if (targetType === "resource") {
      const name = toRoleRoute("resources");
      if (name) await router.push({ name });
      return;
    }
    if (targetType === "forum_topic") {
      const name = toRoleRoute("forum");
      if (name) await router.push({ name });
      return;
    }
    if (targetType === "teamup_post") {
      const name = toRoleRoute("teamup");
      if (name) await router.push({ name });
      return;
    }
    if (targetType === "teacher_post") {
      const name = auth.user?.role === "student" ? "student-projects" : auth.user?.role === "teacher" ? "teacher-posts" : "admin-projects";
      await router.push({ name });
      return;
    }
  }
}


onMounted(() => {
  load();
  timer.value = window.setInterval(load, 15000);
});

onUnmounted(() => {
  if (timer.value) window.clearInterval(timer.value);
});
</script>

<style scoped>
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bell-body {
  max-height: 360px;
  display: flex;
  flex-direction: column;
}

.bell-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
}

.bell-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.bell-item {
  padding: 10px 10px;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid rgba(148, 163, 184, 0.18);
  margin-bottom: 8px;
}

.bell-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.bell-title {
  max-width: 240px;
  font-size: 12px;
  font-weight: 600;
}

.bell-badge {
  font-size: 10px;
}

.bell-summary {
  margin-top: 4px;
  font-size: 12px;
  color: var(--app-muted);
}

.bell-time {
  margin-top: 4px;
  font-size: 11px;
  color: var(--app-muted);
}

.bell-more {
  text-align: center;
  padding: 6px 0 2px;
}
</style>
