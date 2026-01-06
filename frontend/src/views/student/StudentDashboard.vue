<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的学习与科研概览</h2>
        <p class="page-subtitle">基于技能画像、合作记录与匹配推荐生成的个人学习仪表盘</p>
      </div>
      <el-space :size="8">
        <el-button size="small" @click="$router.push({ name: 'student-profile' })">完善画像</el-button>
        <el-button type="primary" size="small" @click="$router.push({ name: 'student-projects' })">浏览项目</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" style="margin-top: 4px;">
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="app-card" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">匹配到的项目</div>
          <div style="font-size: 22px; font-weight: 600;">{{ topProjects.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">基于技能与兴趣的智能推荐</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="app-card" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">当前合作项目</div>
          <div style="font-size: 22px; font-weight: 600;">{{ projects.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">已确认合作的项目数量</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="app-card" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">合作邀请</div>
          <div style="font-size: 22px; font-weight: 600;">{{ invitations.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">老师向你发出的待处理合作邀请</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="dash-main" style="margin-top: 16px;">
      <el-col :xs="24" :lg="16">
        <div class="dash-left">
          <el-card class="app-card dash-card dash-card-match" shadow="never">
            <template #header>
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                  <div class="page-subtitle">匹配到的项目</div>
                  <div style="font-size: 11px; color: var(--app-muted); margin-top: 2px;">根据你的技能和兴趣推荐的项目列表</div>
                </div>
                <el-button link type="primary" size="small" @click="$router.push({ name: 'student-projects' })">
                  查看全部
                </el-button>
              </div>
          </template>
          <el-empty v-if="!topProjects.length" description="还没有匹配记录，可先完善技能画像" />
          <ul v-else style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:10px;">
            <li
              v-for="p in topProjects.slice(0, 2)"
              :key="p.id"
              style="display:flex; align-items:center; justify-content:space-between; gap:8px;"
            >
              <span style="font-size:13px; font-weight:600;" class="truncate">{{ p.title }}</span>
              <span class="pill badge-blue">匹配度 {{ Math.round(p.score * 100) }}%</span>
            </li>
          </ul>
        </el-card>

          <el-card class="app-card dash-card dash-card-projects" shadow="never">
            <template #header>
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <div class="page-subtitle">当前合作项目</div>
                <el-button link type="primary" size="small" @click="$router.push({ name: 'student-cooperation' })">
                  查看进展
                </el-button>
              </div>
            </template>
            <el-empty v-if="!projects.length" description="还没有合作项目，可先浏览教师发布的项目" />
            <el-scrollbar v-else class="dash-table-scroll">
              <div class="project-cards">
                <div 
                  v-for="p in pagedProjects" 
                  :key="p.id" 
                  class="project-card clickable"
                  @click="goToCooperation(p.id)"
                >
                  <div class="project-card-header">
                    <span class="project-title truncate">{{ p.title }}</span>
                    <span class="pill badge-amber">进行中</span>
                  </div>
                  <div v-if="p.upcoming_milestone" class="milestone-info">
                    <el-icon style="color: #f59e0b;"><Clock /></el-icon>
                    <span class="milestone-text">
                      {{ p.upcoming_milestone.title }} - 
                      <span class="milestone-due">{{ formatMilestoneDue(p.upcoming_milestone.due_date) }}</span>
                    </span>
                  </div>
                  <div v-if="p.has_recent_updates" class="update-badge">
                    <span class="update-dot"></span>
                    <span>有新更新</span>
                  </div>
                </div>
              </div>
            </el-scrollbar>
            <div v-if="projects.length > projectPageSize" style="margin-top:8px; text-align:right;">
              <el-pagination
                background
                layout="prev, pager, next"
                :current-page="projectPage"
                :page-size="projectPageSize"
                :total="projects.length"
                @current-change="handleProjectPageChange"
              />
            </div>
          </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="app-card dash-card dash-card-invites" shadow="never">
          <template #header>
            <div class="page-subtitle">合作邀请</div>
          </template>
          <el-empty v-if="!invitations.length" description="暂无合作邀请" />
          <el-scrollbar v-else style="max-height: 180px;">
            <ul style="list-style: none; padding: 0; margin: 0;">
              <li
                v-for="r in invitations.slice(0, 3)"
                :key="r.id"
                style="display: flex; flex-direction: column; gap: 4px; font-size: 12px; padding: 4px 0;"
              >
                <div class="truncate" style="max-width: 220px;">
                  {{ r.teacher?.display_name || '教师' }}
                  邀请你{{ r.post ? `参与 “${r.post.title}”` : '开展合作' }}
                </div>
                <div style="display: flex; gap: 6px;">
                  <el-button type="primary" size="small" text @click="acceptInvite(r)">接受</el-button>
                  <el-button size="small" text @click="rejectInvite(r)">拒绝</el-button>
                </div>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import { ElMessage } from "element-plus";
import { Clock } from "@element-plus/icons-vue";

const router = useRouter();
const topProjects = ref<any[]>([]);
const projects = ref<any[]>([]);
const skills = ref<any[]>([]);
const invitations = ref<any[]>([]);

const projectPage = ref(1);
const projectPageSize = 2;

const pagedProjects = computed(() => {
  const start = (projectPage.value - 1) * projectPageSize;
  return (projects.value || []).slice(start, start + projectPageSize);
});


async function loadMatch() {
  try {
    const resp = await axios.get("/api/match/top");
    if (resp.data.kind === "teacher_posts") {
      topProjects.value = resp.data.items;
    }
  } catch (e) {
  }
}


async function loadProjects() {
  try {
    const resp = await axios.get("/api/cooperation/projects");
    projects.value = resp.data.items;
    projectPage.value = 1;
  } catch (e) {
  }
}


function handleProjectPageChange(p: number) {
  projectPage.value = p;
}


async function loadProfile() {
  try {
    const resp = await axios.get("/api/student-profile");
    skills.value = resp.data.skills || [];
  } catch (e) {
  }
}


async function loadHighlights() {
  try {
    const resp = await axios.get("/api/resources", { params: { category: "活动" } });
  } catch (e) {
  }
}


async function loadInvitations() {
  try {
    const resp = await axios.get("/api/cooperation/requests");
    invitations.value = (resp.data.items || []).filter(
      (r: any) => r.initiated_by === "teacher" && r.student_status === "pending"
    );
  } catch (e) {
  }
}


async function acceptInvite(r: any) {
  await axios.post(`/api/cooperation/requests/${r.id}/respond`, { action: "accept" });
  await loadInvitations();
  ElMessage.success("已接受合作邀请");
}


async function rejectInvite(r: any) {
  await axios.post(`/api/cooperation/requests/${r.id}/respond`, { action: "reject" });
  await loadInvitations();
  ElMessage.success("已拒绝合作邀请");
}


// 跳转到合作进展页面
function goToCooperation(projectId: number) {
  router.push({ name: 'student-cooperation', query: { project: projectId } });
}


// 格式化里程碑截止日期
function formatMilestoneDue(dueDate: string): string {
  if (!dueDate) return '';
  const due = new Date(dueDate);
  const now = new Date();
  const diffTime = due.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) return '已过期';
  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '明天';
  if (diffDays <= 7) return `${diffDays}天后`;
  return due.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}


onMounted(() => {
  loadMatch();
  loadProjects();
  loadProfile();
  loadInvitations();
});
</script>

<style scoped>
.dash-main {
  align-items: stretch;
}

.dash-left {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dash-card {
  overflow: hidden;
}

.dash-card-match {
  height: 170px;
}

.dash-card-projects {
  height: 210px;
}

.dash-card-invites {
  height: 394px;
}

.dash-card :deep(.el-card__body) {
  height: calc(100% - 54px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dash-table-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 项目卡片样式 */
.project-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-card {
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.project-card.clickable {
  cursor: pointer;
}

.project-card.clickable:hover {
  background: #f0f9ff;
  border-color: #93c5fd;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.project-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.project-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  flex: 1;
}

.milestone-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 6px 8px;
  background: #fffbeb;
  border-radius: 6px;
  font-size: 11px;
}

.milestone-text {
  color: #92400e;
}

.milestone-due {
  font-weight: 500;
  color: #d97706;
}

.update-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 11px;
  color: #059669;
}

.update-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
