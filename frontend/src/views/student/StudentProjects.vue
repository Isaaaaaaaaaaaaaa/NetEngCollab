<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">教师项目 / 大创 / 竞赛</h2>
        <p class="page-subtitle">按兴趣和技能筛选项目，并一键发起合作申请</p>
      </div>
      <el-space :size="8">
        <el-input
          v-model="filters.keyword"
          size="small"
          placeholder="关键词，如 深度学习"
          style="width: 220px;"
          clearable
        />
        <el-button size="small" type="primary" plain @click="loadPosts">检索</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="16">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">项目列表</div>
          </template>
          <el-empty v-if="!posts.length" description="暂无项目记录" />
          <el-table
            v-else
            :data="posts"
            size="small"
            border
            style="width: 100%;"
          >
            <el-table-column prop="title" label="项目" min-width="200">
              <template #default="scope">
                <div style="display: flex; flex-direction: column; gap: 2px;">
                  <span style="font-size: 13px; font-weight: 500;" class="truncate">{{ scope.row.title }}</span>
                  <span style="font-size: 11px; color: var(--app-muted);" class="truncate">{{ scope.row.content }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="90" align="center">
              <template #default="scope">
                <span class="pill" :class="scope.row.post_type === 'competition' ? 'badge-amber' : 'badge-blue'">
                  {{ typeLabel(scope.row.post_type) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="技术栈" min-width="140">
              <template #default="scope">
                <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                  <span v-for="t in scope.row.tech_stack" :key="t" class="tag">{{ t }}</span>
                  <span v-for="t in scope.row.tags" :key="t" class="tag">{{ t }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="招募人数" width="90" align="center">
              <template #default="scope">
                <span style="font-size: 12px;">{{ scope.row.recruit_count || "未设置" }}</span>
              </template>
            </el-table-column>
            <el-table-column label="周期/截止" min-width="120" align="center">
              <template #default="scope">
                <div style="display:flex; flex-direction:column; gap:2px;">
                  <span style="font-size:12px;">{{ scope.row.duration || "周期未设定" }}</span>
                  <span style="font-size:11px; color:var(--app-muted);">
                    {{ scope.row.deadline ? scope.row.deadline.slice(0, 10) : "无截止时间" }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="教师" width="100" align="center">
              <template #default="scope">
                <span style="font-size: 12px;">{{ scope.row.teacher?.display_name || "-" }}</span>
              </template>
            </el-table-column>
            <el-table-column label="我的状态" width="110" align="center">
              <template #default="scope">
                <span
                  v-if="requestStatus[scope.row.id]"
                  class="pill"
                  :class="statusClass(requestStatus[scope.row.id])"
                  style="font-size: 11px;"
                >
                  {{ statusLabel(requestStatus[scope.row.id]) }}
                </span>
                <span v-else style="font-size: 11px; color: var(--app-muted);">未申请</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="140" align="right" fixed="right">
              <template #default="scope">
                <el-button
                  size="small"
                  type="primary"
                  text
                  :disabled="!!requestStatus[scope.row.id] && requestStatus[scope.row.id].final_status !== 'rejected'"
                  @click="apply(scope.row)"
                >
                  申请加入
                </el-button>
                <el-button size="small" text @click="favorite(scope.row)">收藏</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div style="display: flex; flex-direction: column; gap: 14px;">
          <el-card class="app-card" shadow="never">
            <template #header>
              <div class="page-subtitle">智能匹配推荐 TOP10</div>
            </template>
            <el-empty v-if="!matched.length" description="暂无匹配结果，可先完善技能画像和兴趣标签" />
            <el-scrollbar v-else style="max-height: 260px;">
              <ul style="list-style: none; padding: 0; margin: 0;">
                <li
                  v-for="p in matched"
                  :key="p.id"
                  style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; padding: 4px 0; gap: 8px;"
                >
                  <span class="truncate" style="max-width: 180px;">{{ p.title }}</span>
                  <span class="pill badge-green">匹配度 {{ Math.round(p.score * 100) }}%</span>
                </li>
              </ul>
            </el-scrollbar>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import axios from "axios";


const posts = ref<any[]>([]);
const matched = ref<any[]>([]);
const filters = reactive({ keyword: "" });
const requestStatus = reactive<Record<number, any>>({});


function typeLabel(t: string) {
  if (t === "competition") return "学科竞赛";
  if (t === "innovation") return "大创项目";
  return "科研项目";
}


async function loadPosts() {
  const resp = await axios.get("/api/teacher-posts", { params: { keyword: filters.keyword || undefined } });
  posts.value = resp.data.items;
}


async function loadMatch() {
  const resp = await axios.get("/api/match/top");
  if (resp.data.kind === "teacher_posts") {
    matched.value = resp.data.items;
  }
}


async function loadMyRequests() {
  const resp = await axios.get("/api/cooperation/requests");
  const map: Record<number, any> = {};
  (resp.data.items || []).forEach((r: any) => {
    if (r.post && r.post.id) {
      map[r.post.id] = r;
    }
  });
  Object.keys(requestStatus).forEach(k => delete requestStatus[Number(k)]);
  Object.entries(map).forEach(([k, v]) => {
    requestStatus[Number(k)] = v;
  });
}


function statusLabel(r: any) {
  if (r.final_status === "confirmed") return "已确认";
  if (r.final_status === "rejected") return "已拒绝";
  if (r.teacher_status === "accepted" && r.student_status === "pending") return "待我确认";
  if (r.teacher_status === "pending" && r.student_status === "accepted") return "待教师确认";
  return "待审核";
}


function statusClass(r: any) {
  if (r.final_status === "confirmed") return "badge-green";
  if (r.final_status === "rejected") return "badge-amber";
  return "badge-blue";
}


async function apply(p: any) {
  const respMe = await axios.get("/api/auth/me");
  const studentId = respMe.data.id;
  await axios.post("/api/cooperation/request", {
    post_id: p.id,
    student_user_id: studentId
  });
  await loadMyRequests();
  alert("已提交合作申请，等待教师确认");
}


async function favorite(p: any) {
  await axios.post("/api/reactions/toggle", {
    target_type: "teacher_post",
    target_id: p.id,
    reaction_type: "favorite"
  });
}


onMounted(() => {
  loadPosts();
  loadMatch();
  loadMyRequests();
});
</script>
