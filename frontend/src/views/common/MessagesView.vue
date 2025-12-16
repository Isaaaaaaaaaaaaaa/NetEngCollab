<template>
  <div class="page msg-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">站内私信</h2>
        <p class="page-subtitle">与合作老师 / 学生进行一对一沟通</p>
      </div>
    </div>

    <el-row :gutter="16" class="msg-row" style="margin-top: 6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card msg-card" shadow="never">
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
              <div class="page-subtitle">会话</div>
              <el-input
                v-model="search"
                size="small"
                placeholder="搜索"
                clearable
                style="width: 180px;"
              />
            </div>
          </template>
          <el-empty v-if="!filteredConversations.length" description="暂无会话" />
          <el-scrollbar v-else class="msg-conv-scroll">
            <ul style="list-style:none; padding:0; margin:0; padding-right:6px;">
              <li
                v-for="c in filteredConversations"
                :key="c.id"
                class="conv-item"
                :class="c.id === selectedId ? 'is-active' : ''"
                @click="select(c.id)"
              >
                <div class="conv-avatar">{{ avatarText(c.other?.display_name) }}</div>
                <div class="conv-main">
                  <div class="conv-top">
                    <span class="conv-name truncate">{{ c.other?.display_name || '用户' }}</span>
                    <span class="conv-time">{{ formatListTime(c.last_at) }}</span>
                  </div>
                  <div class="conv-bottom">
                    <span class="conv-preview truncate">{{ c.last_message || ' ' }}</span>
                    <span v-if="c.unread" class="conv-unread">{{ c.unread }}</span>
                  </div>
                </div>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="app-card msg-card" shadow="never">
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <div class="page-subtitle">{{ activeOther?.display_name || '消息' }}</div>
              <div v-if="activeOther" style="font-size:12px; color:var(--app-muted);">{{ roleLabel(activeOther.role) }}</div>
            </div>
          </template>
          <div ref="scrollEl" class="chat-body">
            <div v-if="!messagesWithMeta.length" style="font-size:12px; color:var(--app-muted); text-align:center; padding:24px 0;">
              选择左侧会话开始聊天。
            </div>
            <template v-else>
              <div
                v-for="m in messagesWithMeta"
                :key="m.key"
              >
                <div v-if="m.kind === 'day'" class="chat-day">{{ m.text }}</div>
                <div v-else class="chat-row" :class="m.mine ? 'is-mine' : ''">
                  <div v-if="!m.mine" class="chat-avatar">{{ avatarText(activeOther?.display_name) }}</div>
                  <div class="chat-bubble">
                    <div class="chat-text">{{ m.content || '[文件]' }}</div>
                    <div class="chat-meta">{{ formatTime(m.created_at) }}</div>
                  </div>
                  <div v-if="m.mine" class="chat-avatar mine">{{ avatarText(me?.display_name) }}</div>
                </div>
              </div>
            </template>
          </div>

          <div class="chat-input">
            <el-input
              v-model="content"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 4 }"
              placeholder="输入消息，Enter 发送，Shift+Enter 换行"
              @keydown.enter.exact.prevent="send"
            />
            <el-button type="primary" :disabled="!selectedId" @click="send">发送</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import axios from "axios";


const conversations = ref<any[]>([]);
const messages = ref<any[]>([]);
const selectedId = ref<number | null>(null);
const content = ref("");
const me = ref<any>(null);
const search = ref("");
const scrollEl = ref<HTMLElement | null>(null);


async function loadConversations() {
  const resp = await axios.get("/api/conversations");
  conversations.value = resp.data.items;
  if (!selectedId.value && conversations.value.length) {
    await select(conversations.value[0].id);
  }
}


async function select(id: number) {
  selectedId.value = id;
  const resp = await axios.get(`/api/conversations/${id}/messages`);
  messages.value = resp.data.items.map((m: any) => ({
    ...m,
    mine: m.sender_user_id === me.value.id
  }));
  await nextTick();
  if (scrollEl.value) {
    scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
  }
}


async function send() {
  if (!content.value.trim() || !selectedId.value) return;
  const conv = conversations.value.find(x => x.id === selectedId.value);
  if (!conv || !conv.other) return;
  const teacherId = me.value.role === "teacher" ? me.value.id : conv.other.role === "teacher" ? conv.other.id : conv.other.id;
  const studentId = me.value.role === "student" ? me.value.id : conv.other.role === "student" ? conv.other.id : conv.other.id;
  await axios.post("/api/messages/send", {
    teacher_user_id: teacherId,
    student_user_id: studentId,
    content: content.value.trim()
  });
  content.value = "";
  await loadConversations();
  await select(selectedId.value);
}


const filteredConversations = computed(() => {
  const kw = (search.value || "").trim();
  if (!kw) return conversations.value;
  return conversations.value.filter((c: any) => (c.other?.display_name || "").includes(kw) || (c.last_message || "").includes(kw));
});


const activeOther = computed(() => {
  const conv = conversations.value.find((x: any) => x.id === selectedId.value);
  return conv?.other || null;
});


const messagesWithMeta = computed(() => {
  const result: any[] = [];
  let lastDay = "";
  (messages.value || []).forEach((m: any) => {
    const day = (m.created_at || "").slice(0, 10);
    if (day && day !== lastDay) {
      lastDay = day;
      result.push({ kind: "day", key: `day-${day}`, text: day });
    }
    result.push({ kind: "msg", key: `msg-${m.id}`, ...m });
  });
  return result;
});


function avatarText(name?: string) {
  const t = (name || "").trim();
  return t ? t.slice(0, 1) : "U";
}


function roleLabel(role?: string) {
  if (role === "teacher") return "教师";
  if (role === "student") return "学生";
  return "";
}


function formatTime(iso?: string) {
  if (!iso) return "";
  return iso.slice(11, 16);
}


function formatListTime(iso?: string) {
  if (!iso) return "";
  const d = iso.slice(0, 10);
  const t = iso.slice(11, 16);
  const today = new Date().toISOString().slice(0, 10);
  return d === today ? t : d.slice(5);
}


onMounted(async () => {
  const meResp = await axios.get("/api/auth/me");
  me.value = meResp.data;
  await loadConversations();
});
</script>

<style scoped>
.msg-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.msg-row {
  flex: 1 1 auto;
  min-height: 0;
  max-height: calc(100vh - 160px);
  overflow: hidden;
}

.msg-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.msg-row :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.msg-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.msg-conv-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.conv-item {
  display: flex;
  gap: 10px;
  padding: 10px 10px;
  border-radius: 12px;
  cursor: pointer;
}

.conv-item:hover {
  background: rgba(148, 163, 184, 0.12);
}

.conv-item.is-active {
  background: rgba(59, 130, 246, 0.12);
}

.conv-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.22), rgba(16, 185, 129, 0.18));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #0f172a;
}

.conv-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conv-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.conv-name {
  font-size: 13px;
  font-weight: 600;
  max-width: 180px;
}

.conv-time {
  font-size: 11px;
  color: var(--app-muted);
}

.conv-bottom {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.conv-preview {
  font-size: 12px;
  color: var(--app-muted);
  max-width: 210px;
}

.conv-unread {
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.chat-body {
  flex: 1;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 14px;
  padding: 12px;
  overflow: auto;
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.08), rgba(255, 255, 255, 0));
}

.chat-day {
  text-align: center;
  font-size: 11px;
  color: var(--app-muted);
  margin: 10px 0;
}

.chat-row {
  display: flex;
  gap: 8px;
  margin: 8px 0;
  align-items: flex-end;
}

.chat-row.is-mine {
  justify-content: flex-end;
}

.chat-avatar {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #0f172a;
}

.chat-avatar.mine {
  background: rgba(34, 197, 94, 0.16);
}

.chat-bubble {
  max-width: 70%;
  padding: 10px 12px;
  border-radius: 14px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.chat-row.is-mine .chat-bubble {
  background: #1677ff;
  border: 1px solid rgba(22, 119, 255, 0.28);
  color: #fff;
}

.chat-text {
  font-size: 13px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-meta {
  font-size: 10px;
  opacity: 0.72;
  margin-top: 4px;
  text-align: right;
}

.chat-input {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 14px;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
