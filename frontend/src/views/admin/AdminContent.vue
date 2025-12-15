<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">内容审核</h2>
        <p class="page-subtitle">拦截不合规范的项目和竞赛信息、资源内容</p>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="12">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">教师项目信息审核</div>
          </template>
          <el-empty v-if="!posts.length" description="暂无待审核项目" />
          <el-table
            v-else
            :data="posts"
            size="small"
            border
            style="width: 100%;"
          >
            <el-table-column label="标题" min-width="200">
              <template #default="scope">
                <span class="truncate" style="max-width:200px;">{{ scope.row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="90" align="center">
              <template #default="scope">
                <span class="pill badge-blue" style="font-size:10px;">{{ scope.row.post_type }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" align="center">
              <template #default="scope">
                <el-button type="primary" size="small" text @click="reviewPost(scope.row, 'approve')">通过</el-button>
                <el-button size="small" text @click="reviewPost(scope.row, 'reject')">拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">资源内容审核</div>
          </template>
          <el-empty v-if="!resources.length" description="暂无待审核资源" />
          <el-table
            v-else
            :data="resources"
            size="small"
            border
            style="width: 100%;"
          >
            <el-table-column label="标题" min-width="200">
              <template #default="scope">
                <span class="truncate" style="max-width:200px;">{{ scope.row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="90" align="center">
              <template #default="scope">
                <span class="pill badge-amber" style="font-size:10px;">{{ scope.row.resource_type }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" align="center">
              <template #default="scope">
                <el-button type="primary" size="small" text @click="reviewRes(scope.row, 'approve')">通过</el-button>
                <el-button size="small" text @click="reviewRes(scope.row, 'reject')">拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const posts = ref<any[]>([]);
const resources = ref<any[]>([]);


async function load() {
  const [postsResp, resResp] = await Promise.all([
    axios.get("/api/admin/pending-teacher-posts"),
    axios.get("/api/admin/pending-resources")
  ]);
  posts.value = postsResp.data.items;
  resources.value = resResp.data.items;
}


async function reviewPost(p: any, action: string) {
  await axios.post(`/api/admin/teacher-posts/${p.id}/review`, { action });
  await load();
}


async function reviewRes(r: any, action: string) {
  await axios.post(`/api/admin/resources/${r.id}/review`, { action });
  await load();
}


onMounted(() => {
  load();
});
</script>
