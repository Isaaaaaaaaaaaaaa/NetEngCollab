<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的项目与学生概览</h2>
        <p class="page-subtitle">帮助你快速了解项目进展、合作情况以及候选学生质量</p>
      </div>
      <el-button type="primary" size="small" @click="$router.push({ name: 'teacher-posts' })">
        发布新项目
      </el-button>
    </div>

    <el-row :gutter="16" style="margin-top: 4px;">
      <el-col :xs="24" :sm="6">
        <el-card class="app-card" shadow="never" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">已发布项目</div>
          <div style="font-size: 22px; font-weight: 600;">{{ posts.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">包含科研、大创和竞赛项目</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card class="app-card" shadow="never" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">合作项目</div>
          <div style="font-size: 22px; font-weight: 600;">{{ projects.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">已确认合作的项目数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card class="app-card" shadow="never" body-style="padding: 14px 16px;">
          <div class="page-subtitle" style="margin-bottom: 4px;">待处理请求</div>
          <div style="font-size: 22px; font-weight: 600;">{{ requests.length }}</div>
          <div style="font-size: 11px; color: var(--app-muted); margin-top: 4px;">来自学生的合作申请</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :xs="24" :lg="16">
        <div style="display: flex; flex-direction: column; gap: 14px;">
          <el-card class="app-card" shadow="never">
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
            <el-timeline v-else>
              <el-timeline-item
                v-for="p in posts"
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
          </el-card>

          <!-- 当前合作模块已移除（合作管理请进入“合作项目进度管理”页面） -->
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div style="display: flex; flex-direction: column; gap: 14px;">
          <el-card class="app-card" shadow="never">
            <template #header>
              <div class="page-subtitle">合作请求</div>
            </template>
            <el-empty v-if="!requests.length" description="暂无新的合作请求" />
            <el-scrollbar v-else style="max-height: 200px;">
              <ul style="list-style: none; padding: 0; margin: 0;">
                <li
                  v-for="r in requests"
                  :key="r.id"
                  style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; padding: 4px 0; gap: 8px;"
                >
                  <div class="truncate" style="max-width: 160px;">
                    {{ r.student?.display_name || "学生" }} 申请加入 {{ r.post?.title || "项目" }}
                  </div>
                  <div style="display: flex; gap: 4px;">
                    <el-button type="primary" size="small" text @click="accept(r)">接受</el-button>
                    <el-button size="small" text @click="reject(r)">拒绝</el-button>
                  </div>
                </li>
              </ul>
            </el-scrollbar>
          </el-card>

          <!-- 推荐学生列表已移至学生画像与匹配页面的排序功能中 -->
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const posts = ref<any[]>([]);
const projects = ref<any[]>([]);
const requests = ref<any[]>([]);


async function loadPosts() {
  const meResp = await axios.get("/api/auth/me");
  const resp = await axios.get("/api/teacher-posts");
  posts.value = resp.data.items.filter((x: any) => x.teacher && x.teacher.id === meResp.data.id);
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
});
</script>
