<template>
  <div class="page au-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">人员概览</h2>
        <p class="page-subtitle">查看所有师生账号信息，支持筛选、重置密码与批量创建</p>
      </div>
      <el-space :size="8">
        <el-select v-model="roleFilter" size="small" style="width: 140px;">
          <el-option label="全部角色" value="" />
          <el-option label="学生" value="student" />
          <el-option label="教师" value="teacher" />
          <el-option label="管理员" value="admin" />
        </el-select>
        <el-input
          v-model="keyword"
          size="small"
          clearable
          placeholder="学号/工号/姓名"
          style="width: 220px;"
        />
        <el-button size="small" @click="load(true)">筛选</el-button>
        <el-button size="small" @click="batchVisible = true">批量创建</el-button>
        <el-button type="primary" size="small" @click="createVisible = true">创建账号</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" class="au-main" style="margin-top:6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card au-card" shadow="never">
          <template #header>
            <div class="page-subtitle">人员列表</div>
          </template>
          <el-empty v-if="!users.length" description="暂无账号" />
          <div v-else class="list-wrap">
            <el-scrollbar class="au-scroll">
              <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text); padding-right:6px;">
                <li
                  v-for="u in users"
                  :key="u.id"
                  style="padding:6px 8px; border-radius:8px; cursor:pointer;"
                  :style="u.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                  @click="select(u)"
                >
                  <div style="display:flex; align-items:center; justify-content:space-between; gap:6px;">
                    <span class="truncate" style="max-width:150px;">{{ u.display_name || u.username }}</span>
                    <span class="pill badge-blue" style="font-size:11px;">{{ roleLabel(u.role) }}</span>
                  </div>
                  <div style="font-size:11px; color:var(--app-muted);">
                    {{ usernameLabel(u.role) }}：{{ u.username }}
                  </div>
                </li>
              </ul>
            </el-scrollbar>

            <div class="pager" v-if="total > pageSize">
              <el-pagination
                background
                layout="prev, pager, next"
                :current-page="page"
                :page-size="pageSize"
                :total="total"
                @current-change="handlePageChange"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="app-card au-card" shadow="never">
          <template #header>
            <div class="page-subtitle">账号详情</div>
          </template>
          <div v-if="!currentDetail" style="font-size:12px; color:var(--app-muted);">请在左侧选择一个账号。</div>
          <el-scrollbar v-else class="au-scroll">
            <div style="font-size:13px; display:flex; flex-direction:column; gap:8px; padding-right:6px;">
              <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                <div>
                  <div style="font-size:15px; font-weight:600;">{{ currentDetail.user.display_name || currentDetail.user.username }}</div>
                  <div style="font-size:12px; color:var(--app-muted);">{{ usernameLabel(currentDetail.user.role) }}：{{ currentDetail.user.username }}</div>
                </div>
                <el-button size="small" type="primary" text @click="openReset(currentDetail.user)">重置密码</el-button>
              </div>
              <div>角色：{{ roleLabel(currentDetail.user.role) }}</div>
              <div>邮箱：{{ currentDetail.user.email || '未填写' }}</div>
              <div>手机号：{{ currentDetail.user.phone || '未填写' }}</div>
              <div>状态：{{ currentDetail.user.is_active ? '已启用' : '未启用' }}</div>
              <div>注册时间：{{ currentDetail.user.created_at?.slice(0, 16).replace('T', ' ') }}</div>

              <el-divider content-position="left">基础信息</el-divider>
              <div v-if="currentDetail.user.role === 'student'">
                <div v-if="currentDetail.student_profile">
                  <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:12px;">
                    <span>专业：{{ currentDetail.student_profile.major || '未填写' }}</span>
                    <span>年级：{{ currentDetail.student_profile.grade || '未填写' }}</span>
                    <span>班级：{{ currentDetail.student_profile.class_name || '未填写' }}</span>
                    <span>每周投入：{{ currentDetail.student_profile.weekly_hours ? (currentDetail.student_profile.weekly_hours + ' 小时') : '未填写' }}</span>
                  </div>
                  <div style="margin-top:8px;">
                    技能：
                    <span v-if="!currentDetail.student_profile.skills?.length" style="color:var(--app-muted);">未填写</span>
                  </div>
                  <div v-if="currentDetail.student_profile.skills?.length" style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">
                    <span v-for="sk in currentDetail.student_profile.skills" :key="sk.name + sk.level" class="tag">{{ sk.name }} · {{ sk.level }}</span>
                  </div>
                  <div style="margin-top:8px;">
                    兴趣：
                    <span v-if="!currentDetail.student_profile.interests?.length" style="color:var(--app-muted);">未填写</span>
                  </div>
                  <div v-if="currentDetail.student_profile.interests?.length" style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">
                    <span v-for="t in currentDetail.student_profile.interests" :key="t" class="tag">{{ t }}</span>
                  </div>
                  <div style="margin-top:8px;">
                    项目经历：
                    <span v-if="!currentDetail.student_profile.experiences?.length" style="color:var(--app-muted);">暂无</span>
                  </div>
                  <ul v-if="currentDetail.student_profile.experiences?.length" style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
                    <li v-for="(e, idx) in currentDetail.student_profile.experiences" :key="idx" style="padding:6px 0; border-bottom:1px solid rgba(148,163,184,0.16);">
                      <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                        <span class="truncate" style="max-width:260px; font-weight:500;">{{ e.title || '未命名项目' }}</span>
                        <span style="font-size:11px; color:var(--app-muted);">{{ e.time || '' }}</span>
                      </div>
                      <div style="font-size:11px; color:var(--app-muted);">{{ e.type || '' }} · {{ e.outcome || '' }}</div>
                    </li>
                  </ul>
                </div>
                <div v-else style="font-size:12px; color:var(--app-muted);">该学生尚未完善画像。</div>
              </div>

              <div v-else-if="currentDetail.user.role === 'teacher'">
                <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:12px;">
                  <span>已发布项目：{{ currentDetail.stats?.published_posts ?? 0 }}</span>
                  <span>已确认合作：{{ currentDetail.stats?.confirmed_projects ?? 0 }}</span>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="createVisible" title="创建账号" width="420px">
      <el-form :model="createForm" label-position="top" size="small">
        <el-form-item :label="usernameLabel(createForm.role)">
          <el-input v-model="createForm.username" :placeholder="usernamePlaceholder(createForm.role)" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="createForm.display_name" placeholder="如：张三" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="createForm.password" type="password" placeholder="默认 123456" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align:right;">
          <el-button size="small" @click="createVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="createUser">创建</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置密码" width="360px">
      <el-form :model="resetForm" label-position="top" size="small">
        <el-form-item label="新密码">
          <el-input v-model="resetForm.password" type="password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align:right;">
          <el-button size="small" @click="resetVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="resetPassword">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="batchVisible" title="批量创建账号" width="520px">
      <el-form label-position="top" size="small">
        <el-form-item label="导入格式">
          <div style="font-size:12px; color:var(--app-muted); line-height: 1.55;">
            每行一条：角色,学号/工号,姓名,初始密码(可选)
            <br />示例：student,221002501,张三,123456
            <br />示例：teacher,10010001,李老师
          </div>
        </el-form-item>
        <el-form-item label="批量内容">
          <el-input v-model="batchText" type="textarea" :rows="8" placeholder="粘贴多行数据" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align:right;">
          <el-button size="small" @click="batchVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="batchCreate">创建</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";


const users = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const roleFilter = ref<string>("");
const keyword = ref("");
const selectedId = ref<number | null>(null);
const createVisible = ref(false);
const createForm = ref({ username: "", display_name: "", role: "student", password: "" });
const resetVisible = ref(false);
const resetForm = ref({ id: 0, password: "" });
const currentDetail = ref<any | null>(null);
const batchVisible = ref(false);
const batchText = ref("");


async function load(resetPage = false) {
  if (resetPage) {
    page.value = 1;
    selectedId.value = null;
    currentDetail.value = null;
  }

  try {
    const resp = await axios.get("/api/admin/users", {
      params: {
        role: roleFilter.value || undefined,
        keyword: keyword.value || undefined,
        page: page.value,
        page_size: pageSize.value
      }
    });
    users.value = resp.data.items || [];
    total.value = resp.data.total || 0;

    if (!users.value.length && page.value > 1) {
      page.value = 1;
      return await load(false);
    }

    if (users.value.length && !selectedId.value) {
      try {
        await select(users.value[0]);
      } catch (e) {
        currentDetail.value = null;
      }
    }
  } catch (e) {
    users.value = [];
    total.value = 0;
    currentDetail.value = null;
  }
}


function handlePageChange(p: number) {
  page.value = p;
  selectedId.value = null;
  currentDetail.value = null;
  load();
}


async function createUser() {
  if (!createForm.value.username) return;
  await axios.post("/api/admin/users/batch-create", {
    users: [
      {
        username: createForm.value.username,
        display_name: createForm.value.display_name || createForm.value.username,
        role: createForm.value.role,
        password: createForm.value.password || "123456"
      }
    ]
  });
  createVisible.value = false;
  createForm.value = { username: "", display_name: "", role: "student", password: "" };
  await load();
}


function roleLabel(role: string) {
  if (role === "student") return "学生";
  if (role === "teacher") return "教师";
  if (role === "admin") return "管理员";
  return role;
}


function usernameLabel(role: string) {
  if (role === "student") return "学号";
  if (role === "teacher") return "工号";
  return "用户名";
}


function usernamePlaceholder(role: string) {
  if (role === "student") return "如：221002501";
  if (role === "teacher") return "如：10010001";
  return "如：admin01";
}


const parsedBatchUsers = computed(() => {
  const lines = (batchText.value || "")
    .split(/\r?\n/)
    .map(s => s.trim())
    .filter(Boolean);
  const out: any[] = [];
  for (const line of lines) {
    const parts = line.split(/\s*,\s*/);
    const role = (parts[0] || "").trim();
    const username = (parts[1] || "").trim();
    const display_name = (parts[2] || username).trim();
    const password = (parts[3] || "123456").trim();
    if (!username) continue;
    if (!role || !["student", "teacher"].includes(role)) continue;
    out.push({ role, username, display_name, password });
  }
  return out;
});


async function batchCreate() {
  const usersToCreate = parsedBatchUsers.value;
  if (!usersToCreate.length) return;
  const resp = await axios.post("/api/admin/users/batch-create", { users: usersToCreate });
  const created = resp.data?.created || [];
  batchVisible.value = false;
  batchText.value = "";
  alert(`已创建 ${created.length} 个账号`);
  page.value = 1;
  selectedId.value = null;
  currentDetail.value = null;
  await load();
}


function openReset(u: any) {
  resetForm.value = { id: u.id, password: "" };
  resetVisible.value = true;
}


async function resetPassword() {
  if (!resetForm.value.password) return;
  await axios.post(`/api/admin/users/${resetForm.value.id}/set-password`, {
    password: resetForm.value.password
  });
  resetVisible.value = false;
}


async function select(u: any) {
  selectedId.value = u.id;
  const resp = await axios.get(`/api/admin/users/${u.id}`);
  currentDetail.value = resp.data;
}


onMounted(() => {
  load(true);
});
</script>

<style scoped>
.au-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.au-main {
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
  overflow: hidden;
}

.au-main :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.au-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.au-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.list-wrap {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.au-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.pager {
  margin-top: 8px;
  text-align: right;
  flex: 0 0 auto;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
