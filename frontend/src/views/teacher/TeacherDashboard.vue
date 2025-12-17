<template>
  <div class="page teacher-dash">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的项目与学生概览</h2>
        <p class="page-subtitle">帮助你快速了解项目进展、合作情况以及候选学生质量</p>
      </div>
      <el-button type="primary" size="small" @click="$router.push({ name: 'teacher-posts' })">
        发布新项目
      </el-button>
    </div>

    <el-row :gutter="16" class="stat-row" style="margin-top: 4px;">
      <el-col :xs="24" :sm="8" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">已发布项目</div>
          <div style="font-size: 22px; font-weight: 600;">{{ posts.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">包含科研、大创和竞赛项目</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">合作项目</div>
          <div style="font-size: 22px; font-weight: 600;">{{ projects.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">已确认合作的项目数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">待处理请求</div>
          <div style="font-size: 22px; font-weight: 600;">{{ requests.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">来自学生的合作申请</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="app-card" shadow="never" style="margin-top: 14px;">
      <template #header>
        <div class="page-subtitle">我的教师信息</div>
      </template>
      <el-form :model="profile" label-position="top" size="small">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12">
            <el-form-item label="职称">
              <el-input v-model="profile.title" placeholder="如：副教授" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="单位/团队">
              <el-input v-model="profile.organization" placeholder="如：网络安全实验室" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="研究方向标签（逗号分隔）">
          <el-input v-model="researchTagsInput" placeholder="如：网络安全, 深度学习" />
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input v-model="profile.bio" type="textarea" :rows="3" placeholder="简要描述研究方向、指导方式等" />
        </el-form-item>
        <div style="text-align:right;">
          <el-button size="small" type="primary" :disabled="saving" @click="saveProfile">保存</el-button>
        </div>
      </el-form>
      <div v-if="savedHint" style="margin-top:8px; font-size:12px; color:#16a34a;">已保存，学生侧展示将同步更新。</div>
    </el-card>

    <el-row :gutter="16" class="dash-main" style="margin-top: 16px;">
      <el-col :xs="24" :lg="16">
        <el-card class="app-card dash-card dash-card-recent" shadow="never">
          <template #header>
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <div>
                <div class="page-subtitle">最近发布的项目</div>
                <div style="font-size: 11px; color: var(--app-muted); margin-top: 2px;">最近发布的项目按时间倒序展示</div>
              </div>
              <el-button link type="primary" size="small" @click="$router.push({ name: 'teacher-posts' })">
                管理项目
              </el-button>
            </div>
          </template>

          <el-empty v-if="!posts.length" description="还没有发布项目" />
          <el-scrollbar v-else class="dash-scroll">
            <el-timeline style="padding-right: 6px;">
              <el-timeline-item
                v-for="p in pagedPosts"
                :key="p.id"
                size="small"
                type="primary"
              >
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                  <div style="font-size: 13px; font-weight: 500;" class="truncate">{{ p.title }}</div>
                  <div class="pill badge-blue">{{ p.post_type }}</div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-scrollbar>

          <div v-if="posts.length > postsPageSize" style="text-align:right; margin-top: 8px; flex: 0 0 auto;">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="postsPage"
              :page-size="postsPageSize"
              :total="posts.length"
              @current-change="handlePostsPageChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="app-card dash-card dash-card-requests" shadow="never">
          <template #header>
            <div class="page-subtitle">合作请求</div>
          </template>

          <el-empty v-if="!requests.length" description="暂无新的合作请求" />
          <el-scrollbar v-else class="dash-scroll">
            <ul style="list-style: none; padding: 0; margin: 0; padding-right: 6px;">
              <li
                v-for="r in pagedRequests"
                :key="r.id"
                style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; padding: 6px 0; gap: 8px;"
              >
                <div class="truncate" style="max-width: 240px;">
                  {{ r.student?.display_name || "学生" }} 申请加入 {{ r.post?.title || "项目" }}
                </div>
                <div class="btns">
                  <el-button type="primary" size="small" text @click="accept(r)">接受</el-button>
                  <el-button size="small" text @click="reject(r)">拒绝</el-button>
                </div>
              </li>
            </ul>
          </el-scrollbar>

          <div v-if="requests.length > requestsPageSize" style="text-align:right; margin-top: 8px; flex: 0 0 auto;">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="requestsPage"
              :page-size="requestsPageSize"
              :total="requests.length"
              @current-change="handleRequestsPageChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import axios from "axios";


const posts = ref<any[]>([]);
const projects = ref<any[]>([]);
const requests = ref<any[]>([]);

const profile = reactive({
  title: "",
  organization: "",
  bio: ""
});
const researchTagsInput = ref("");
const saving = ref(false);
const savedHint = ref(false);

const postsPage = ref(1);
const postsPageSize = 5;
const requestsPage = ref(1);
const requestsPageSize = 5;

const pagedPosts = computed(() => {
  const start = (postsPage.value - 1) * postsPageSize;
  return (posts.value || []).slice(start, start + postsPageSize);
});

const pagedRequests = computed(() => {
  const start = (requestsPage.value - 1) * requestsPageSize;
  return (requests.value || []).slice(start, start + requestsPageSize);
});


async function loadPosts() {
  const meResp = await axios.get("/api/auth/me");
  const resp = await axios.get("/api/teacher-posts");
  posts.value = resp.data.items.filter((x: any) => x.teacher && x.teacher.id === meResp.data.id);
  postsPage.value = 1;
}


async function loadProjects() {
  const resp = await axios.get("/api/cooperation/projects");
  projects.value = resp.data.items;
}




async function loadRequests() {
  const resp = await axios.get("/api/cooperation/requests");
  requests.value = resp.data.items.filter(
    (x: any) => x.teacher_status === "pending" && x.initiated_by === "student"
  );
  requestsPage.value = 1;
}


async function loadProfile() {
  try {
    const resp = await axios.get("/api/teacher-profile");
    profile.title = resp.data?.title || "";
    profile.organization = resp.data?.organization || "";
    profile.bio = resp.data?.bio || "";
    researchTagsInput.value = (resp.data?.research_tags || []).join(", ");
  } catch (e) {
  }
}


async function saveProfile() {
  saving.value = true;
  try {
    const tags = researchTagsInput.value
      .split(/[,，]/)
      .map(x => x.trim())
      .filter(x => x);
    await axios.put("/api/teacher-profile", {
      title: profile.title || null,
      organization: profile.organization || null,
      bio: profile.bio || null,
      research_tags: tags
    });
    savedHint.value = true;
    setTimeout(() => {
      savedHint.value = false;
    }, 3000);
  } catch (e) {
  } finally {
    saving.value = false;
  }
}


function handlePostsPageChange(p: number) {
  postsPage.value = p;
}


function handleRequestsPageChange(p: number) {
  requestsPage.value = p;
}


async function accept(r: any) {
  await axios.post(`/api/cooperation/requests/${r.id}/respond`, { action: "accept" });
  await loadRequests();
}


async function reject(r: any) {
  await axios.post(`/api/cooperation/requests/${r.id}/respond`, { action: "reject" });
  await loadRequests();
}


onMounted(() => {
  loadPosts();
  loadProjects();
  loadRequests();
  loadProfile();
});
</script>

<style scoped>
.dash-main {
  align-items: stretch;
}

.dash-main :deep(.el-col) {
  display: flex;
  flex-direction: column;
}

.dash-card {
  height: 420px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dash-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dash-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.dash-scroll :deep(.el-scrollbar__view) {
  padding-top: 10px;
}

.btns {
  display: flex;
  gap: 6px;
  white-space: nowrap;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
