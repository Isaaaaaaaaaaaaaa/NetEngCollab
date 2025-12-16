<template>
  <div class="page proj-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">教师项目 / 大创 / 竞赛</h2>
        <p class="page-subtitle">按兴趣和技能筛选项目，并一键发起合作申请</p>
      </div>
      <el-space :size="8">
        <el-radio-group v-model="reactFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="liked">我点赞的</el-radio-button>
          <el-radio-button label="favorited">我收藏的</el-radio-button>
        </el-radio-group>
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

    <el-row :gutter="16" class="proj-main" style="margin-top: 6px;">
      <el-col :xs="24" :lg="16">
        <el-card class="app-card proj-card proj-card-list" shadow="never">
          <template #header>
            <div class="page-subtitle">项目列表</div>
          </template>
          <el-table
            :data="postsDisplay"
            size="small"
            border
            style="width: 100%;"
          >
            <el-table-column prop="title" label="项目" min-width="200">
              <template #default="scope">
                <div v-if="scope.row.__placeholder" style="font-size:12px; color:var(--app-muted);">暂无</div>
                <div style="display: flex; flex-direction: column; gap: 2px;">
                  <span style="font-size: 13px; font-weight: 500;" class="truncate">{{ scope.row.title }}</span>
                  <span style="font-size: 11px; color: var(--app-muted);" class="truncate">{{ scope.row.content }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="90" align="center">
              <template #default="scope">
                <span v-if="scope.row.__placeholder" style="font-size:12px; color:var(--app-muted);">-</span>
                <span class="pill" :class="scope.row.post_type === 'competition' ? 'badge-amber' : 'badge-blue'">
                  {{ typeLabel(scope.row.post_type) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="技术栈" min-width="140">
              <template #default="scope">
                <span v-if="scope.row.__placeholder" style="font-size:12px; color:var(--app-muted);">-</span>
                <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                  <span v-for="t in scope.row.tech_stack" :key="t" class="tag">{{ t }}</span>
                  <span v-for="t in scope.row.tags" :key="t" class="tag">{{ t }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="招募人数" width="90" align="center">
              <template #default="scope">
                <span v-if="scope.row.__placeholder" style="font-size:12px; color:var(--app-muted);">-</span>
                <span style="font-size: 12px;">{{ scope.row.recruit_count || "未设置" }}</span>
              </template>
            </el-table-column>
            <el-table-column label="周期/截止" min-width="120" align="center">
              <template #default="scope">
                <span v-if="scope.row.__placeholder" style="font-size:12px; color:var(--app-muted);">-</span>
                <div style="display:flex; flex-direction:column; gap:2px;">
                  <span style="font-size:12px;">{{ scope.row.duration || "周期未设定" }}</span>
                  <span style="font-size:11px; color:var(--app-muted);">
                    {{ scope.row.deadline ? scope.row.deadline.slice(0, 10) : "无截止时间" }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="教师" width="120" align="center">
              <template #default="scope">
                <span v-if="scope.row.__placeholder" style="font-size: 12px; color:var(--app-muted);">-</span>
                <el-link
                  v-if="scope.row.teacher"
                  type="primary"
                  :underline="false"
                  style="font-size:12px;"
                  @click.stop="chat(scope.row)"
                >
                  {{ scope.row.teacher.display_name }}
                </el-link>
                <span v-else style="font-size: 12px;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="我的状态" width="110" align="center">
              <template #default="scope">
                <span v-if="scope.row.__placeholder" style="font-size: 11px; color: var(--app-muted);">-</span>
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
            <el-table-column label="互动" width="220" align="right">
              <template #default="scope">
                <InteractionsPanel
                  v-if="!scope.row.__placeholder"
                  :target-type="'teacher_post'"
                  :target-id="scope.row.id"
                  :enable-comments="false"
                  @changed="handleInteractionChanged"
                />
                <span v-else style="font-size: 11px; color: var(--app-muted);">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="120" align="right" fixed="right">
              <template #default="scope">
                <el-button
                  size="small"
                  type="primary"
                  text
                  :disabled="scope.row.__placeholder || (!!requestStatus[scope.row.id] && requestStatus[scope.row.id].final_status !== 'rejected')"
                  @click="apply(scope.row)"
                >
                  申请加入
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="total > pageSize" style="margin-top:8px; text-align:right;">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="page"
              :page-size="pageSize"
              :total="total"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="proj-right">
          <el-card class="app-card proj-card proj-card-match" shadow="never">
            <template #header>
              <div class="page-subtitle">智能匹配推荐 TOP10</div>
            </template>
            <ul class="top10-list">
              <li
                v-for="(p, idx) in matchedDisplay"
                :key="p.id"
                class="top10-item"
                :class="idx === matchedDisplay.length - 1 ? 'is-last' : ''"
              >
                <span class="truncate" style="max-width: 180px; color: var(--app-text);">
                  {{ p.__placeholder ? "暂无推荐" : p.title }}
                </span>
                <span v-if="!p.__placeholder" class="pill badge-green">匹配度 {{ Math.round(p.score * 100) }}%</span>
                <span v-else style="font-size: 11px; color: var(--app-muted);">-</span>
              </li>
            </ul>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import InteractionsPanel from "../../components/InteractionsPanel.vue";


const posts = ref<any[]>([]);
const matched = ref<any[]>([]);
const filters = reactive({ keyword: "" });
const requestStatus = reactive<Record<number, any>>({});
const router = useRouter();
const reactFilter = ref<"all" | "liked" | "favorited">("all");
const page = ref(1);
const pageSize = ref(5);
const total = ref(0);

const postsDisplay = computed(() => {
  const out: any[] = (posts.value || []).map((p: any) => ({ ...p, __placeholder: false }));
  const target = pageSize.value;
  for (let i = out.length; i < target; i++) {
    out.push({ id: -1 * (page.value * 100 + i + 1), __placeholder: true });
  }
  return out;
});

const matchedDisplay = computed(() => {
  const out: any[] = (matched.value || []).slice(0, 10).map((p: any) => ({ ...p, __placeholder: false }));
  for (let i = out.length; i < 10; i++) {
    out.push({ id: `ph-${i}`, __placeholder: true });
  }
  return out;
});


function typeLabel(t: string) {
  if (t === "competition") return "学科竞赛";
  if (t === "innovation") return "大创项目";
  return "科研项目";
}


async function loadPosts() {
  const resp = await axios.get("/api/teacher-posts", {
    params: {
      keyword: filters.keyword || undefined,
      like_only: reactFilter.value === "liked" ? 1 : undefined,
      favorite_only: reactFilter.value === "favorited" ? 1 : undefined,
      page: page.value,
      page_size: pageSize.value
    }
  });
  posts.value = resp.data.items;
  total.value = resp.data.total || 0;
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


function handlePageChange(p: number) {
  page.value = p;
  loadPosts();
}


function handleInteractionChanged() {
  if (reactFilter.value !== "all") {
    loadPosts();
  }
}


async function chat(p: any) {
  if (!p.teacher || !p.teacher.id) return;
  const meResp = await axios.get("/api/auth/me");
  const me = meResp.data;
  await axios.post("/api/messages/send", {
    teacher_user_id: p.teacher.id,
    student_user_id: me.id,
    content: `老师您好，我对您的项目“${p.title}”很感兴趣，想进一步了解。`
  });
  router.push({ name: "student-messages" });
}


onMounted(() => {
  loadPosts();
  loadMatch();
  loadMyRequests();
});


watch(reactFilter, () => {
  page.value = 1;
  loadPosts();
});
</script>

<style scoped>
.proj-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.proj-main {
  align-items: stretch;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.proj-main :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.proj-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.proj-card-list {
  min-height: 360px;
}

.proj-card-match {
  min-height: 360px;
}

.proj-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.proj-card-list :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
}

.proj-card-list :deep(.el-table) {
  flex: 1 1 auto;
}

.proj-card-match :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}

.proj-right {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}

.top10-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.top10-item {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  padding: 0 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.top10-item.is-last {
  border-bottom: none;
}
</style>
