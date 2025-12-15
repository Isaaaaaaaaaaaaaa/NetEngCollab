<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">人员概览</h2>
        <p class="page-subtitle">查看所有老师和同学账号信息，并支持筛选与重置密码</p>
      </div>
      <el-space :size="8">
        <el-select v-model="roleFilter" size="small" style="width: 140px;">
          <el-option label="全部角色" value="" />
          <el-option label="学生" value="student" />
          <el-option label="教师" value="teacher" />
          <el-option label="管理员" value="admin" />
        </el-select>
        <el-button size="small" @click="load">筛选</el-button>
        <el-button type="primary" size="small" @click="createVisible = true">创建账号</el-button>
      </el-space>
    </div>

    <el-row :gutter="16" style="margin-top:6px;">
      <el-col :xs="24" :lg="8">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">人员列表</div>
          </template>
          <el-empty v-if="!users.length" description="暂无账号" />
          <el-scrollbar v-else style="max-height: 320px;">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="u in users"
                :key="u.id"
                style="padding:6px 8px; border-radius:8px; cursor:pointer;"
                :style="u.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                @click="select(u)"
              >
                <div style="display:flex; align-items:center; justify-content:space-between; gap:6px;">
                  <span class="truncate" style="max-width:150px;">{{ u.display_name || u.username }}</span>
                  <span class="pill badge-blue" style="font-size:11px;">{{ u.role }}</span>
                </div>
                <div style="font-size:11px; color:var(--app-muted);">{{ u.username }}</div>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
        <div style="margin-top:8px; text-align:center;">
          <el-pagination
            v-if="total > pageSize"
            background
            layout="prev, pager, next"
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            @current-change="handlePageChange"
          />
        </div>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">账号详情</div>
          </template>
          <div v-if="!current" style="font-size:12px; color:var(--app-muted);">请在左侧选择一个账号。</div>
          <div v-else style="font-size:13px; display:flex; flex-direction:column; gap:8px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
              <div>
                <div style="font-size:15px; font-weight:600;">{{ current.display_name || current.username }}</div>
                <div style="font-size:12px; color:var(--app-muted);">{{ current.username }}</div>
              </div>
              <el-button size="small" type="primary" text @click="openReset(current)">重置密码</el-button>
            </div>
            <div>角色：{{ current.role }}</div>
            <div>邮箱：{{ current.email || '未填写' }}</div>
            <div>手机号：{{ current.phone || '未填写' }}</div>
            <div>状态：{{ current.is_active ? '已启用' : '未启用' }}</div>
            <div>注册时间：{{ current.created_at?.slice(0, 16).replace('T', ' ') }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="createVisible" title="创建账号" width="420px">
      <el-form :model="createForm" label-position="top" size="small">
        <el-form-item label="用户名">
          <el-input v-model="createForm.username" placeholder="如：stu202501" />
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";


const users = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const roleFilter = ref<string>("");
const selectedId = ref<number | null>(null);
const createVisible = ref(false);
const createForm = ref({ username: "", display_name: "", role: "student", password: "" });
const resetVisible = ref(false);
const resetForm = ref({ id: 0, password: "" });
const current = ref<any | null>(null);


async function load() {
  const resp = await axios.get("/api/admin/users", {
    params: { role: roleFilter.value || undefined, page: page.value, page_size: pageSize.value }
  });
  users.value = resp.data.items;
  total.value = resp.data.total || 0;
  if (users.value.length && !selectedId.value) {
    selectedId.value = users.value[0].id;
    current.value = users.value[0];
  }
}


function handlePageChange(p: number) {
  page.value = p;
  selectedId.value = null;
  current.value = null;
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


function select(u: any) {
  selectedId.value = u.id;
  current.value = u;
}


onMounted(() => {
  load();
});
</script>
