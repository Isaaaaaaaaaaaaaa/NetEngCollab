<template>
  <div class="page cp-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">合作项目进度管理</h2>
        <p class="page-subtitle">里程碑、进度更新与成果一体化管理</p>
      </div>
    </div>

    <el-row :gutter="16" class="cp-main" style="margin-top: 6px;">
      <el-col :xs="24" :lg="6">
        <el-card class="app-card cp-card" shadow="never">
          <template #header>
            <div class="page-subtitle">我的合作项目</div>
          </template>
          <el-empty v-if="!projects.length" description="暂无合作项目" />
          <el-scrollbar v-else class="cp-scroll">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="p in projects"
                :key="p.id"
                style="padding:8px; border-radius:8px; cursor:pointer; margin-bottom: 4px;"
                :style="p.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                @click="select(p.id)"
              >
                <div style="font-weight: 500; margin-bottom: 4px;" class="truncate">{{ p.title }}</div>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--app-muted);">
                  <span class="pill" :class="p.project_status === 'in_progress' ? 'badge-green' : (p.project_status === 'completed' ? 'badge-gray' : 'badge-blue')" style="font-size: 10px;">
                    {{ p.project_status === 'in_progress' ? '进行中' : (p.project_status === 'completed' ? '已完成' : '招募中') }}
                  </span>
                  <span>{{ p.student_count || 0 }} 名学生</span>
                </div>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="app-card cp-card" shadow="never">
          <template #header>
            <div class="page-subtitle">里程碑</div>
          </template>
          <el-empty v-if="!selectedId" description="请选择左侧项目" />
          <div v-else class="cp-section">
            <el-empty v-if="!milestones.length" description="暂无里程碑，可在下方添加" />
            <el-scrollbar v-else class="cp-scroll" style="padding-right: 6px;">
              <el-timeline>
                <el-timeline-item
                  v-for="m in milestones"
                  :key="m.id"
                  size="small"
                  :type="m.status === 'done' ? 'success' : m.is_near_due ? 'danger' : 'warning'"
                >
                  <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                    <div style="display:flex; flex-direction:column; gap:2px; max-width:240px;">
                      <span class="truncate">{{ m.title }}</span>
                      <span v-if="m.due_date" style="font-size:10px; color:var(--app-muted);">
                        截止 {{ m.due_date.slice(0, 10) }}
                      </span>
                    </div>
                    <el-button
                      v-if="m.status !== 'done'"
                      size="small"
                      type="primary"
                      text
                      @click.stop="markMilestoneDone(m)"
                    >
                      标记完成
                    </el-button>
                    <span v-else class="pill badge-green">已完成</span>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </el-scrollbar>

            <div class="cp-form">
              <el-input
                v-model="milestoneTitle"
                size="small"
                placeholder="新里程碑标题"
                style="margin-bottom:6px;"
              />
              <el-date-picker
                v-model="milestoneDueDate"
                type="date"
                size="small"
                placeholder="可选：截止日期"
                value-format="YYYY-MM-DD"
                style="width:100%; margin-bottom:6px;"
              />
              <el-button type="primary" plain size="small" style="width:100%;" @click="addMilestone">添加里程碑</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="app-card cp-card" shadow="never">
          <template #header>
            <div class="page-subtitle">进度更新</div>
          </template>
          <el-empty v-if="!selectedId" description="请选择左侧项目" />
          <div v-else class="cp-section">
            <el-empty v-if="!updates.length" description="暂无更新" />
            <el-scrollbar v-else class="cp-scroll">
              <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text); padding-right:6px;">
                <li
                  v-for="u in updates"
                  :key="u.id"
                  style="padding:8px 0; border-bottom:1px solid rgba(148,163,184,0.25);"
                >
                  <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                    <span class="pill badge-blue" style="font-size: 10px;">{{ u.author_name || '未知' }}</span>
                    <span style="font-size:10px; color:var(--app-muted);">
                      {{ u.created_at?.slice(0, 16).replace('T', ' ') }}
                    </span>
                  </div>
                  <div style="white-space: pre-wrap; word-break: break-word;">{{ u.content }}</div>
                </li>
              </ul>
            </el-scrollbar>

            <div class="cp-form">
              <el-input
                v-model="updateContent"
                type="textarea"
                :rows="3"
                placeholder="记录阶段性进展、遇到的问题与下一步计划"
              />
              <el-button
                type="primary"
                size="small"
                style="width:100%; margin-top:6px;"
                @click="addUpdate"
              >
                提交更新
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const projects = ref<any[]>([]);
const selectedId = ref<number | null>(null);
const milestones = ref<any[]>([]);
const updates = ref<any[]>([]);
const milestoneTitle = ref("");
const updateContent = ref("");
const milestoneDueDate = ref("");


async function loadProjects() {
  const resp = await axios.get("/api/cooperation/projects");
  projects.value = resp.data.items;
  if (projects.value.length && !selectedId.value) {
    selectedId.value = projects.value[0].id;
    await loadDetails();
  }
}


async function loadDetails() {
  if (!selectedId.value) return;
  const [msResp, upResp] = await Promise.all([
    axios.get(`/api/posts/${selectedId.value}/milestones`),
    axios.get(`/api/posts/${selectedId.value}/updates`)
  ]);
  milestones.value = msResp.data.items;
  updates.value = upResp.data.items;
}


function select(id: number) {
  selectedId.value = id;
  loadDetails();
}


async function addMilestone() {
  if (!selectedId.value || !milestoneTitle.value) return;
  await axios.post(`/api/posts/${selectedId.value}/milestones`, {
    title: milestoneTitle.value,
    due_date: milestoneDueDate.value || null
  });
  milestoneTitle.value = "";
  milestoneDueDate.value = "";
  await loadDetails();
}


async function markMilestoneDone(m: any) {
  if (!selectedId.value) return;
  await axios.put(`/api/posts/${selectedId.value}/milestones/${m.id}`, {
    status: "done"
  });
  await loadDetails();
}


async function addUpdate() {
  if (!selectedId.value || !updateContent.value) return;
  await axios.post(`/api/posts/${selectedId.value}/updates`, { content: updateContent.value });
  updateContent.value = "";
  await loadDetails();
}


onMounted(() => {
  loadProjects();
});
</script>

<style scoped>
.cp-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cp-main {
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
  overflow: hidden;
}

.cp-main :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.cp-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cp-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cp-section {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.cp-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.cp-form {
  flex: 0 0 auto;
  margin-top: 8px;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
