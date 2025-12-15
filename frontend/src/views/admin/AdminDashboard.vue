<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">平台总体数据</h2>
        <p class="page-subtitle">为专业建设提供数据支撑</p>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">注册用户</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.users }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">包含学生、教师和管理员账号总数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">教师发布项目</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.teacher_posts }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">当前系统中的科研 / 大创 / 竞赛条目</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">资源条目</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.resources }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">用于教学与竞赛的资源文件数量</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">待办事项</div>
      </template>
      <el-row :gutter="16">
        <el-col :xs="24" :lg="8">
          <div class="page-subtitle" style="margin-bottom:6px;">待审核账号</div>
          <el-empty v-if="!pendingUsers.length" description="暂无待审核账号" />
          <ul v-else style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
            <li
              v-for="u in pendingUsers"
              :key="u.id"
              style="display:flex; align-items:center; justify-content:space-between; padding:4px 0;"
            >
              <span>{{ u.username }} · {{ u.role }}</span>
            </li>
          </ul>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div class="page-subtitle" style="margin-bottom:6px;">待审核项目</div>
          <el-empty v-if="!pendingPosts.length" description="暂无待审核项目" />
          <ul v-else style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
            <li
              v-for="p in pendingPosts"
              :key="p.id"
              style="display:flex; align-items:center; justify-content:space-between; padding:4px 0; gap:8px;"
            >
              <span class="truncate" style="max-width:160px;">{{ p.title }}</span>
              <span class="pill badge-blue" style="font-size:10px;">{{ p.post_type }}</span>
            </li>
          </ul>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div class="page-subtitle" style="margin-bottom:6px;">待审核资源</div>
          <el-empty v-if="!pendingResources.length" description="暂无待审核资源" />
          <ul v-else style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
            <li
              v-for="r in pendingResources"
              :key="r.id"
              style="display:flex; align-items:center; justify-content:space-between; padding:4px 0; gap:8px;"
            >
              <span class="truncate" style="max-width:160px;">{{ r.title }}</span>
              <span class="pill badge-amber" style="font-size:10px;">{{ r.resource_type }}</span>
            </li>
          </ul>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">师生合作概览</div>
      </template>
      <div style="font-size:12px; color:var(--app-muted); margin-bottom:8px;">
        结合合作请求统计师生双选的整体情况，便于答辩展示平台成效。
      </div>
      <el-row :gutter="16">
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px;">合作总数</div>
          <div style="font-size:20px; font-weight:600; margin-top:4px;">{{ coopSummary.total }}</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px;">已确认合作</div>
          <div style="font-size:20px; font-weight:600; margin-top:4px; color:#16a34a;">{{ coopSummary.confirmed }}</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px;">待处理 / 已拒绝</div>
          <div style="font-size:20px; font-weight:600; margin-top:4px;">{{ coopSummary.pending }} / {{ coopSummary.rejected }}</div>
        </el-col>
      </el-row>
    </el-card>

  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const stats = ref<any>({ users: 0, teacher_posts: 0, resources: 0 });
const pendingUsers = ref<any[]>([]);
const pendingPosts = ref<any[]>([]);
const pendingResources = ref<any[]>([]);
const coopSummary = ref<any>({ total: 0, confirmed: 0, rejected: 0, pending: 0 });


async function load() {
  const [statsResp, usersResp, postsResp, resResp, coopResp] = await Promise.all([
    axios.get("/api/admin/stats"),
    axios.get("/api/admin/pending-users"),
    axios.get("/api/admin/pending-teacher-posts"),
    axios.get("/api/admin/pending-resources"),
    axios.get("/api/admin/cooperations")
  ]);
  stats.value = statsResp.data;
  pendingUsers.value = usersResp.data.items;
  pendingPosts.value = postsResp.data.items;
  pendingResources.value = resResp.data.items;
  coopSummary.value = coopResp.data.summary || coopSummary.value;
}


onMounted(() => {
  load();
});
</script>
