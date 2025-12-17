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
        人员概览支持分页、重置密码与批量创建账号；项目概览用于查看双选与合作情况；数据分析展示平台活跃度与趋势。
      </div>
    </el-card>

    <el-card class="app-card" shadow="never" style="margin-top:16px;">
      <template #header>
        <div class="page-subtitle">内容治理与活跃概览</div>
      </template>
      <el-row :gutter="12">
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px; margin-bottom:4px;">近 14 天项目发布</div>
          <div style="font-size:20px; font-weight:600;">{{ activity.posts14 }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:2px;">教师项目发布活跃度</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px; margin-bottom:4px;">近 14 天私信沟通</div>
          <div style="font-size:20px; font-weight:600;">{{ activity.msg14 }}</div>
          <div style="font-size:11px; color:var(--app-muted); margin-top:2px;">站内私信产生的消息数量</div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div style="font-size:13px; margin-bottom:4px;">内容治理兜底</div>
          <div style="font-size:12px; color:var(--app-text); line-height:1.6;">
            管理员可在资源库 / 讨论区 / 组队互助中删除违规内容，并可通过私信提醒发布者。
          </div>
        </el-col>
      </el-row>
      <div style="margin-top:10px; display:flex; flex-wrap:wrap; gap:6px;">
        <span style="font-size:12px; color:var(--app-muted);">热门方向：</span>
        <span v-for="t in hotTopics" :key="t.name" class="tag">{{ t.name }} · {{ t.count }}</span>
        <span v-if="!hotTopics.length" style="font-size:12px; color:var(--app-muted);">暂无</span>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";


const stats = ref<any>({ users: 0, teacher_posts: 0, resources: 0 });
const analytics = ref<any>({ posts_daily: [], messages_daily: [], hot_topics: [] });


const activity = computed(() => {
  const posts14 = (analytics.value.posts_daily || []).reduce((sum: number, x: any) => sum + (x.count || 0), 0);
  const msg14 = (analytics.value.messages_daily || []).reduce((sum: number, x: any) => sum + (x.count || 0), 0);
  return { posts14, msg14 };
});


const hotTopics = computed(() => {
  return (analytics.value.hot_topics || []).slice(0, 8);
});


async function load() {
  const [statsResp, analyticsResp] = await Promise.all([
    axios.get("/api/admin/stats"),
    axios.get("/api/admin/analytics")
  ]);
  stats.value = statsResp.data;
  analytics.value = analyticsResp.data;
}


onMounted(() => {
  load();
});
</script>
