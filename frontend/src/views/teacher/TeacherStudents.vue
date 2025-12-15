<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">学生画像与匹配</h2>
        <p class="page-subtitle">按方向、技能和关键词筛选学生，快速找到合适的合作伙伴</p>
      </div>
      <el-space :size="8">
        <el-input
          v-model="filters.keyword"
          size="small"
          placeholder="关键词，如 目标检测"
          style="width: 240px;"
          clearable
        />
        <el-button size="small" type="primary" plain @click="load">检索</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" style="margin-top: 6px;">
      <el-col :xs="24" :lg="14">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">学生列表</div>
          </template>
          <el-empty v-if="!students.length" description="暂无学生记录" />
          <el-table
            v-else
            :data="pagedStudents"
            size="small"
            border
            @row-click="select"
            style="cursor:pointer;"
          >
            <el-table-column label="姓名" min-width="120">
              <template #default="scope">
                <span style="font-size:13px; font-weight:500;">{{ scope.row.user.display_name }}</span>
              </template>
            </el-table-column>
            <el-table-column label="方向" min-width="120">
              <template #default="scope">
                <span style="font-size:12px;">{{ scope.row.direction || '未填写' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="技能" min-width="150">
              <template #default="scope">
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                  <span v-for="sk in scope.row.skills" :key="sk.name" class="tag">{{ sk.name }} · {{ sk.level }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="每周时间" width="100" align="center">
              <template #default="scope">
                <span v-if="scope.row.weekly_hours" style="font-size:12px;">每周 {{ scope.row.weekly_hours }} 小时</span>
                <span v-else style="font-size:12px; color:var(--app-muted);">未填写</span>
              </template>
            </el-table-column>
            <el-table-column label="推荐度" width="110" align="center">
              <template #default="scope">
                <span v-if="recommendScores[scope.row.user.id]" class="pill badge-green" style="font-size:11px;">
                  匹配 {{ Math.round(recommendScores[scope.row.user.id] * 100) }}%
                </span>
                <span v-else style="font-size:11px; color:var(--app-muted);">无</span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="totalStudents > pageSize" style="margin-top:8px; text-align:right;">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="page"
              :page-size="pageSize"
              :total="totalStudents"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">学生详情</div>
          </template>
          <div v-if="!selectedStudent" style="font-size:12px; color:var(--app-muted);">
            在左侧表格中选择一名学生查看详细画像。
          </div>
          <div v-else style="display:flex; flex-direction:column; gap:8px; font-size:13px;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <div style="font-size:15px; font-weight:600;">{{ selectedStudent.user.display_name }}</div>
              <div v-if="selectedStudent.weekly_hours" class="pill badge-green">每周 {{ selectedStudent.weekly_hours }} 小时</div>
            </div>
            <div>方向：{{ selectedStudent.direction || '未填写' }}</div>
            <div>
              技能：
              <span v-if="!selectedStudent.skills.length" style="color:var(--app-muted);">未填写</span>
            </div>
            <div v-if="selectedStudent.skills.length" style="display:flex; flex-wrap:wrap; gap:6px;">
              <span v-for="sk in selectedStudent.skills" :key="sk.name" class="tag">{{ sk.name }} · {{ sk.level }}</span>
            </div>
            <div>
              偏好：
              <span>{{ selectedStudent.prefer_local ? '优先本地' : '可远程' }}</span>
              ·
              <span>{{ selectedStudent.accept_cross ? '接受跨方向' : '方向匹配优先' }}</span>
            </div>
            <div style="margin-top:6px;">
              <div style="font-size:12px; color:var(--app-muted); margin-bottom:4px;">选择合作项目并发送邀请</div>
              <el-select
                v-model="selectedPostId"
                size="small"
                placeholder="请选择一个你的项目"
                style="width:100%; margin-bottom:6px;"
              >
                <el-option
                  v-for="p in myPosts"
                  :key="p.id"
                  :label="p.title"
                  :value="p.id"
                />
              </el-select>
              <div v-if="currentRequest" style="font-size:12px; margin-bottom:6px;">
                当前状态：
                <span class="pill" :class="statusClass(currentRequest)" style="font-size:11px;">
                  {{ statusLabel(currentRequest) }}
                </span>
              </div>
            </div>
            <div style="margin-top:6px; display:flex; gap:8px;">
              <el-button
                type="primary"
                size="small"
                :disabled="!selectedPostId"
                @click="invite(selectedStudent)"
              >
                发出合作邀请
              </el-button>
              <el-button size="small" @click="chat(selectedStudent)">发私信</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import axios from "axios";


const students = ref<any[]>([]);
const filters = reactive({ keyword: "" });
const page = ref(1);
const pageSize = ref(10);
const selectedStudent = ref<any | null>(null);
const myPosts = ref<any[]>([]);
const selectedPostId = ref<number | null>(null);
const currentRequest = ref<any | null>(null);
const recommendScores = reactive<Record<number, number>>({});


async function load() {
  page.value = 1;
  const resp = await axios.get("/api/students", {
    params: { keyword: filters.keyword || undefined }
  });
  students.value = resp.data.items;
  if (!selectedStudent.value && students.value.length) {
    selectedStudent.value = students.value[0];
  }
  const meResp = await axios.get("/api/auth/me");
  const postsResp = await axios.get("/api/teacher-posts");
  myPosts.value = (postsResp.data.items || []).filter((x: any) => x.teacher && x.teacher.id === meResp.data.id);
  if (!selectedPostId.value && myPosts.value.length) {
    selectedPostId.value = myPosts.value[0].id;
  }
  await loadCurrentRequest();

  const matchResp = await axios.get("/api/match/top", { params: { limit: 50 } });
  Object.keys(recommendScores).forEach(k => delete recommendScores[Number(k)]);
  if (matchResp.data.kind === "students") {
    (matchResp.data.items || []).forEach((r: any) => {
      if (r.user_id) {
        recommendScores[r.user_id] = r.score || 0;
      }
    });
  }
}


const sortedStudents = computed(() => {
  return [...students.value].sort((a, b) => {
    const sa = recommendScores[a.user.id] || 0;
    const sb = recommendScores[b.user.id] || 0;
    if (sb !== sa) return sb - sa;
    return (b.weekly_hours || 0) - (a.weekly_hours || 0);
  });
});


const totalStudents = computed(() => sortedStudents.value.length);


const pagedStudents = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return sortedStudents.value.slice(start, start + pageSize.value);
});


function handlePageChange(p: number) {
  page.value = p;
}


async function invite(s: any) {
  if (!selectedPostId.value) return;
  await axios.post("/api/cooperation/request", {
    post_id: selectedPostId.value,
    student_user_id: s.user.id
  });
  await loadCurrentRequest();
  alert("已发送合作邀请，等待学生确认");
}


async function chat(s: any) {
  const me = await axios.get("/api/auth/me");
  await axios.post("/api/messages/send", {
    teacher_user_id: me.data.id,
    student_user_id: s.user.id,
    content: "你好，我对你的技能很感兴趣，方便进一步交流吗？"
  });
  alert("已发送一条私信");
}


function select(row: any) {
  selectedStudent.value = row;
  loadCurrentRequest();
}


async function loadCurrentRequest() {
  if (!selectedStudent.value || !selectedPostId.value) {
    currentRequest.value = null;
    return;
  }
  const resp = await axios.get("/api/cooperation/requests", {
    params: { post_id: selectedPostId.value }
  });
  const items = resp.data.items || [];
  const found = items.find((r: any) => r.student && r.student.id === selectedStudent.value.user.id);
  currentRequest.value = found || null;
}


function statusLabel(r: any) {
  if (r.final_status === "confirmed") return "已确认";
  if (r.final_status === "rejected") return "已拒绝";
  if (r.teacher_status === "accepted" && r.student_status === "accepted") return "待确认";
  if (r.teacher_status === "accepted" && r.student_status === "pending") return "待学生接受";
  if (r.teacher_status === "pending" && r.student_status === "accepted") return "待教师确认";
  if (r.teacher_status === "accepted") return "老师已接受";
  if (r.student_status === "accepted") return "学生已接受";
  return "待处理";
}


function statusClass(r: any) {
  if (r.final_status === "confirmed") return "badge-green";
  if (r.final_status === "rejected") return "badge-amber";
  return "badge-blue";
}


onMounted(() => {
  load();
});
</script>
