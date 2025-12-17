<template>
  <div class="page msg-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">站内私信</h2>
        <div class="msg-subtitle-row">
          <p class="page-subtitle" style="margin:0;">{{ dmHint || '站内私信沟通与文件传输' }}</p>
        </div>
        <div class="msg-toprow">
          <div v-if="me && (me.role === 'student' || me.role === 'teacher')" class="auto-reply-row">
            <span style="white-space:nowrap;">自动回复：</span>
            <el-input
              v-model="autoReplyDraft"
              size="small"
              clearable
              placeholder="可选，如：我会在 24 小时内回复"
              style="width: 360px;"
            />
            <el-button size="small" :disabled="savingAutoReply" @click="saveAutoReply">保存</el-button>
          </div>
          <div v-if="me && (me.role === 'student' || me.role === 'teacher')" class="auto-reply-rule">
            规则：对方发来消息触发；同一会话 12 小时最多回复一次；清空即关闭。
          </div>
        </div>
      </div>
    </div>

    <el-row :gutter="16" class="msg-row" style="margin-top: 6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card msg-card" shadow="never">
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
              <div class="page-subtitle">会话</div>
              <div style="display:flex; align-items:center; gap:8px;">
                <el-input
                  v-model="search"
                  size="small"
                  placeholder="搜索"
                  clearable
                  style="width: 180px;"
                />
                <el-button v-if="me && me.role === 'admin'" size="small" @click="openStart">新建</el-button>
              </div>
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
                    <div class="chat-text">
                      <span v-if="m.is_auto_reply" class="auto-reply-tag">【自动回复】</span>
                      <span v-if="m.file" class="file-line" :class="m.mine ? 'is-mine' : 'is-other'">
                        <el-link
                          class="file-link"
                          :underline="false"
                          :style="m.mine ? 'color:#ffffff;' : ''"
                          @click.prevent="downloadFile(m.file)"
                        >
                          {{ m.file.original_name || '[文件]' }}
                        </el-link>
                        <span v-if="m.file.size_bytes" class="file-size">({{ formatSize(m.file.size_bytes) }})</span>
                      </span>
                      <span v-else>{{ m.display_content || '' }}</span>
                    </div>
                    <div class="chat-meta">{{ formatTime(m.created_at) }}</div>
                  </div>
                  <div v-if="m.mine" class="chat-avatar mine">{{ avatarText(me?.display_name) }}</div>
                </div>
              </div>
            </template>
          </div>

          <div class="chat-input">
            <input ref="fileInputEl" type="file" style="display:none;" @change="handlePickFile" />
            <el-input
              v-model="content"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 4 }"
              placeholder="输入消息，Enter 发送，Shift+Enter 换行"
              @keydown.enter.exact.prevent="send"
            />
            <el-button :disabled="!selectedId || uploading" @click="pickFile">发送文件</el-button>
            <el-button type="primary" :disabled="!selectedId || uploading" @click="send">发送</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="startVisible" title="新建会话" width="520px">
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
        <el-input v-model="startKeyword" size="small" clearable placeholder="学号/工号/姓名" style="flex:1;" />
        <el-button size="small" type="primary" plain :disabled="startLoading" @click="searchUsers">搜索</el-button>
      </div>
      <el-empty v-if="!startUsers.length" description="暂无结果" />
      <el-scrollbar v-else style="max-height: 340px;">
        <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text); padding-right:6px;">
          <li
            v-for="u in startUsers"
            :key="u.id"
            style="padding:8px 10px; border-radius:10px; cursor:pointer; border:1px solid rgba(148,163,184,0.22); margin-bottom:8px;"
            @click="startWith(u)"
          >
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
              <span class="truncate" style="max-width:260px; font-weight:600;">{{ u.display_name || u.username }}</span>
              <span class="pill" :class="u.role === 'teacher' ? 'badge-blue' : u.role === 'student' ? 'badge-amber' : 'badge-gray'" style="font-size:10px;">
                {{ u.role === 'teacher' ? '教师' : u.role === 'student' ? '学生' : '管理员' }}
              </span>
            </div>
            <div style="font-size:11px; color:var(--app-muted); margin-top:2px;">账号：{{ u.username }}</div>
          </li>
        </ul>
      </el-scrollbar>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";


const conversations = ref<any[]>([]);
const messages = ref<any[]>([]);
const selectedId = ref<number | null>(null);
const content = ref("");
const me = ref<any>(null);
const search = ref("");
const scrollEl = ref<HTMLElement | null>(null);
const fileInputEl = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const autoReplyDraft = ref("");
const savingAutoReply = ref(false);

const startVisible = ref(false);
const startKeyword = ref("");
const startUsers = ref<any[]>([]);
const startLoading = ref(false);

const route = useRoute();


const dmHint = computed(() => {
  const role = me.value?.role;
  if (role === "teacher") {
    return "提示：在“学生画像与匹配”中选择学生后，点击“发私信”即可向学生发送私信。";
  }
  if (role === "student") {
    return "提示：在“项目与匹配”列表点击教师姓名，即可向教师发起私信沟通。";
  }
  if (role === "admin") {
    return "提示：点击左侧“新建”可搜索用户并发起提醒私信。";
  }
  return "";
});


async function loadAutoReply() {
  if (!me.value) return;
  if (me.value.role !== "student" && me.value.role !== "teacher") return;
  try {
    const resp = await axios.get("/api/messages/auto-reply");
    autoReplyDraft.value = resp.data?.auto_reply || "";
  } catch (e) {
  }
}


async function saveAutoReply() {
  if (!me.value) return;
  if (me.value.role !== "student" && me.value.role !== "teacher") return;
  savingAutoReply.value = true;
  try {
    await axios.put("/api/messages/auto-reply", { auto_reply: autoReplyDraft.value });
  } catch (e) {
  } finally {
    savingAutoReply.value = false;
  }
}


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
    mine: m.sender_user_id === me.value.id,
    is_auto_reply: typeof m.content === "string" && m.content.startsWith("【自动回复】"),
    display_content:
      typeof m.content === "string" && m.content.startsWith("【自动回复】")
        ? m.content.replace(/^【自动回复】\s?/, "")
        : m.content
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
  const teacherId = conv.teacher_user_id;
  const studentId = conv.student_user_id;
  await axios.post("/api/messages/send", {
    teacher_user_id: teacherId,
    student_user_id: studentId,
    content: content.value.trim()
  });
  content.value = "";
  await loadConversations();
  await select(selectedId.value);
}


function pickFile() {
  if (!selectedId.value) return;
  fileInputEl.value?.click();
}


async function handlePickFile(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || !selectedId.value) return;

  const conv = conversations.value.find(x => x.id === selectedId.value);
  if (!conv || !conv.other) return;

  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file);
    const up = await axios.post("/api/files", fd);
    const fileId = up.data?.file_id;
    if (!fileId) return;
    const teacherId = conv.teacher_user_id;
    const studentId = conv.student_user_id;
    await axios.post("/api/messages/send", {
      teacher_user_id: teacherId,
      student_user_id: studentId,
      file_id: fileId
    });
    await loadConversations();
    await select(selectedId.value);
  } catch (err) {
  } finally {
    uploading.value = false;
  }
}


function formatSize(bytes: number) {
  if (!bytes || bytes <= 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}


async function downloadFile(file: any) {
  if (!file || !file.id) return;
  const resp = await axios.get(`/api/files/${file.id}`, { responseType: "blob" });
  const blobUrl = window.URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = file.original_name || `file_${file.id}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(blobUrl);
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
  await loadAutoReply();
  await loadConversations();
  const cid = Number(route.query.conversation_id);
  if (cid && conversations.value.some((x: any) => x.id === cid)) {
    await select(cid);
  }
});


function openStart() {
  startUsers.value = [];
  startKeyword.value = "";
  startVisible.value = true;
}


async function searchUsers() {
  if (!me.value || me.value.role !== "admin") return;
  startLoading.value = true;
  try {
    const resp = await axios.get("/api/admin/users", {
      params: { keyword: (startKeyword.value || "").trim() || undefined, page: 1, page_size: 30 }
    });
    startUsers.value = resp.data.items || [];
  } catch (e) {
    startUsers.value = [];
  } finally {
    startLoading.value = false;
  }
}


async function startWith(u: any) {
  if (!me.value || me.value.role !== "admin") return;
  if (!u || !u.id) return;
  try {
    const resp = await axios.post("/api/conversations/start", { user_id: u.id });
    const cid = resp.data?.id;
    startVisible.value = false;
    await loadConversations();
    if (cid) {
      await select(cid);
    }
  } catch (e) {
  }
}
</script>

<style scoped>
.msg-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.msg-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--app-muted);
}

.msg-subtitle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 2px;
}

.msg-toprow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 6px;
}

.auto-reply-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--app-muted);
  font-size: 12px;
}

.auto-reply-rule {
  font-size: 12px;
  color: var(--app-muted);
  text-align: right;
}

.auto-reply-tag {
  display: inline-block;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  margin-right: 6px;
  background: rgba(148, 163, 184, 0.22);
  color: #0f172a;
}

.chat-row.is-mine .auto-reply-tag {
  background: rgba(255, 255, 255, 0.24);
  color: #fff;
}

.file-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

:deep(.file-link) {
  color: var(--el-color-primary);
}

.chat-row.is-mine :deep(.file-link) {
  color: #fff;
}

.chat-row.is-mine .file-size {
  color: rgba(255, 255, 255, 0.85);
}

.file-size {
  font-size: 11px;
  color: var(--app-muted);
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
