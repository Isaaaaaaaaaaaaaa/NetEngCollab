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
                <el-button link type="primary" size="small" @click="$router.push({ name: 'student-projects' })">
                  查看项目
                </el-button>
              </div>
            </template>
            <el-empty v-if="!projects.length" description="还没有合作项目，可先浏览教师发布的项目" />
            <el-table
              v-else
              :data="projects.slice(0, 3)"
              size="small"
              style="width: 100%;"
              border
              :show-header="false"
            >
              <el-table-column prop="title" min-width="200">
                <template #default="scope">
                  <span style="font-size: 13px;" class="truncate">{{ scope.row.title }}</span>
                </template>
              </el-table-column>
              <el-table-column width="90" align="right">
                <template #default>
                  <span class="pill badge-amber">进行中</span>
                </template>
              </el-table-column>
            </el-table>
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
import { onMounted, ref } from "vue";
import axios from "axios";


const topProjects = ref<any[]>([]);
const projects = ref<any[]>([]);
const skills = ref<any[]>([]);
const invitations = ref<any[]>([]);


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
  } catch (e) {
  }
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
}


async function rejectInvite(r: any) {
  await axios.post(`/api/cooperation/requests/${r.id}/respond`, { action: "reject" });
  await loadInvitations();
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
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
