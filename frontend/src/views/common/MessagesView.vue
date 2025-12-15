<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">站内私信</h2>
        <p class="page-subtitle">与合作老师 / 学生进行一对一沟通</p>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">会话列表</div>
          </template>
          <el-empty v-if="!conversations.length" description="暂无会话" />
          <el-scrollbar v-else style="max-height: 420px;">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="c in conversations"
                :key="c.id"
                style="display:flex; align-items:center; justify-content:space-between; padding:6px 8px; border-radius:8px; cursor:pointer;"
                :style="c.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                @click="select(c.id)"
              >
                <span class="truncate" style="max-width:140px;">{{ c.other?.display_name || '用户' }}</span>
                <span v-if="c.unread" class="pill badge-amber" style="font-size:10px;">未读 {{ c.unread }}</span>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="app-card" shadow="never" style="display:flex; flex-direction:column; height:100%;">
          <template #header>
            <div class="page-subtitle">消息内容</div>
          </template>
          <div style="flex:1; border:1px solid rgba(148,163,184,0.4); border-radius:10px; padding:8px; overflow:auto; font-size:12px; display:flex; flex-direction:column; gap:6px;">
            <div
              v-for="m in messages"
              :key="m.id"
              :style="m.mine ? 'align-self:flex-end;' : 'align-self:flex-start;'"
            >
              <div
                :style="m.mine
                  ? 'background:#1677ff; color:#fff; border-radius:14px 14px 4px 14px;'
                  : 'background:#f3f4ff; color:#111827; border-radius:14px 14px 14px 4px;'
                "
                style="max-width:70%; padding:6px 10px; box-shadow:0 2px 6px rgba(15,23,42,0.12);"
              >
                <div>{{ m.content || '[文件]' }}</div>
                <div style="font-size:10px; opacity:0.7; margin-top:2px; text-align:right;">
                  {{ m.created_at?.slice(11, 16) }}
                </div>
              </div>
            </div>
            <div v-if="!messages.length" style="font-size:11px; color:var(--app-muted);">
              选择左侧会话查看历史消息。
            </div>
          </div>
          <form style="margin-top:8px; display:flex; gap:8px;" @submit.prevent="send">
            <el-input v-model="content" placeholder="输入要发送的消息" />
            <el-button type="primary" native-type="submit">发送</el-button>
          </form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const conversations = ref<any[]>([]);
const messages = ref<any[]>([]);
const selectedId = ref<number | null>(null);
const content = ref("");
const me = ref<any>(null);


async function loadConversations() {
  const resp = await axios.get("/api/conversations");
  conversations.value = resp.data.items;
}


async function select(id: number) {
  selectedId.value = id;
  const resp = await axios.get(`/api/conversations/${id}/messages`);
  messages.value = resp.data.items.map((m: any) => ({
    ...m,
    mine: m.sender_user_id === me.value.id
  }));
}


async function send() {
  if (!content.value || !selectedId.value) return;
  const conv = conversations.value.find(x => x.id === selectedId.value);
  if (!conv || !conv.other) return;
  const teacherId = me.value.role === "teacher" ? me.value.id : conv.other.role === "teacher" ? conv.other.id : conv.other.id;
  const studentId = me.value.role === "student" ? me.value.id : conv.other.role === "student" ? conv.other.id : conv.other.id;
  await axios.post("/api/messages/send", {
    teacher_user_id: teacherId,
    student_user_id: studentId,
    content: content.value
  });
  content.value = "";
  await select(selectedId.value);
}


onMounted(async () => {
  const meResp = await axios.get("/api/auth/me");
  me.value = meResp.data;
  await loadConversations();
});
</script>
