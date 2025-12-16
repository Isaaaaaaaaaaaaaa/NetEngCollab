<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">管理员总览</h2>
        <p class="page-subtitle">账号管理、项目概览与平台数据分析入口</p>
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
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">科研 / 大创 / 竞赛项目总数</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never" body-style="padding:14px 16px;">
          <div class="page-subtitle" style="margin-bottom:4px;">资源条目</div>
          <div style="font-size: 24px; font-weight: 600;">{{ stats.resources }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:4px;">教学与竞赛资源文件数量</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">功能导航</div>
      </template>
      <el-row :gutter="12">
        <el-col :xs="24" :lg="8">
          <el-button type="primary" plain style="width:100%;" @click="$router.push({ name: 'admin-users' })">人员概览</el-button>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-button type="primary" plain style="width:100%;" @click="$router.push({ name: 'admin-projects' })">项目概览</el-button>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-button type="primary" plain style="width:100%;" @click="$router.push({ name: 'admin-analytics' })">数据分析</el-button>
        </el-col>
      </el-row>
      <div style="margin-top:10px; font-size:12px; color:var(--app-muted);">
        人员概览支持分页、重置密码与批量创建账号；项目概览用于审核与查看项目情况；数据分析展示平台活跃度与趋势。
      </div>
    </el-card>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">待办提醒</div>
      </template>
      <el-row :gutter="12">
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px; margin-bottom:4px;">待审核项目</div>
          <div style="font-size:20px; font-weight:600;">{{ pending.teacher_posts }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:2px;">来自教师发布的项目，需管理员审核</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px; margin-bottom:4px;">待审核资源</div>
          <div style="font-size:20px; font-weight:600;">{{ pending.resources }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:2px;">学生/教师上传的教学与竞赛资源</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px; margin-bottom:4px;">待激活账号</div>
          <div style="font-size:20px; font-weight:600;">{{ pending.users }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:2px;">尚未启用的师生账号</div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const stats = ref<any>({ users: 0, teacher_posts: 0, resources: 0 });
const pending = ref<any>({ teacher_posts: 0, resources: 0, users: 0 });


async function load() {
  const [statsResp, postsResp, resResp, usersResp] = await Promise.all([
    axios.get("/api/admin/stats"),
    axios.get("/api/admin/pending-teacher-posts"),
    axios.get("/api/admin/pending-resources"),
    axios.get("/api/admin/pending-users")
  ]);
  stats.value = statsResp.data;
  pending.value.teacher_posts = postsResp.data.items.length;
  pending.value.resources = resResp.data.items.length;
  pending.value.users = usersResp.data.items.length;
}


onMounted(() => {
  load();
});
</script>
