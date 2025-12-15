<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">项目概览</h2>
        <p class="page-subtitle">查看所有教师项目及其学生选择情况</p>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top:6px;">
      <el-col :xs="24" :lg="7">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">项目列表</div>
          </template>
          <el-empty v-if="!projects.length" description="暂无项目" />
          <el-scrollbar v-else style="max-height: 320px;">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="p in projects"
                :key="p.id"
                style="padding:6px 8px; border-radius:8px; cursor:pointer; display:flex; flex-direction:column; gap:2px;"
                :style="p.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                @click="select(p.id)"
              >
                <div style="display:flex; align-items:center; justify-content:space-between; gap:6px;">
                  <span class="truncate" style="max-width:160px; font-weight:500;">{{ p.title }}</span>
                  <span class="pill badge-blue" style="font-size:11px;">{{ p.post_type }}</span>
                </div>
                <div style="font-size:11px; color:var(--app-muted);">
                  {{ p.teacher?.display_name || '未知教师' }} · 已选择 {{ p.selected_students.length }} 人
                </div>
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

      <el-col :xs="24" :lg="17">
        <el-card class="app-card" shadow="never">
          <template #header>
            <div class="page-subtitle">项目详情</div>
          </template>
          <div v-if="!current" style="font-size:12px; color:var(--app-muted);">请在左侧选择一个项目。</div>
          <div v-else style="display:flex; flex-direction:column; gap:8px; font-size:13px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
              <div style="font-size:15px; font-weight:600;" class="truncate">{{ current.title }}</div>
              <span class="pill badge-blue" style="font-size:11px;">{{ current.post_type }}</span>
            </div>
            <div>教师：{{ current.teacher?.display_name || '未知' }}（{{ current.teacher?.username }}）</div>
            <div>简介：{{ current.content }}</div>
            <div>招募人数：{{ current.recruit_count || '未设置' }}</div>
            <div>项目周期：{{ current.duration || '未设置' }}</div>
            <div>预期成果与要求：{{ current.outcome || '未填写' }}</div>
            <div>联系方式：{{ current.contact || '未填写' }}</div>
            <div>
              报名截止时间：{{ current.deadline ? current.deadline.slice(0, 10) : '未设置' }}
            </div>
            <el-divider content-position="left">学生选择情况</el-divider>
            <el-empty v-if="!current.selected_students.length" description="暂无学生选择该项目" />
            <el-table
              v-else
              :data="current.selected_students"
              size="small"
              border
              style="width:100%;"
            >
              <el-table-column label="学生" min-width="140">
                <template #default="scope">
                  <span>{{ scope.row.student?.display_name || '学生' }}（{{ scope.row.student?.username }}）</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="140" align="center">
                <template #default="scope">
                  <span class="pill" :class="statusClass(scope.row)" style="font-size:11px;">
                    {{ statusLabel(scope.row) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <el-divider content-position="left">管理员操作</el-divider>
            <div style="display:flex; gap:8px;">
              <el-button size="small" type="primary" text @click="openEdit(current)">编辑项目</el-button>
              <el-button size="small" type="danger" text @click="remove(current)">删除项目</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
    <el-dialog v-model="editVisible" title="编辑项目信息" width="520px">
      <el-form :model="editForm" label-position="top" size="small">
        <el-form-item label="项目类型">
          <el-select v-model="editForm.post_type">
            <el-option label="科研项目" value="project" />
            <el-option label="大创项目" value="innovation" />
            <el-option label="学科竞赛" value="competition" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="项目简介">
          <el-input v-model="editForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="招募人数">
          <el-input-number v-model="editForm.recruit_count" :min="1" :max="99" controls-position="right" />
        </el-form-item>
        <el-form-item label="项目周期">
          <el-input v-model="editForm.duration" />
        </el-form-item>
        <el-form-item label="预期成果与要求">
          <el-input v-model="editForm.outcome" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="editForm.contact" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align:right;">
          <el-button size="small" @click="editVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="saveEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";


const projects = ref<any[]>([]);
const selectedId = ref<number | null>(null);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);

const editVisible = ref(false);
const editForm = ref({
  id: 0,
  title: "",
  content: "",
  post_type: "project",
  recruit_count: null as number | null,
  duration: "",
  outcome: "",
  contact: ""
});


const current = computed(() => projects.value.find(p => p.id === selectedId.value) || null);


function statusLabel(row: any) {
  if (row.final_status === "confirmed") return "已确认";
  if (row.final_status === "rejected") return "已拒绝";
  if (row.teacher_status === "accepted" && row.student_status === "pending") return "待学生接受";
  if (row.teacher_status === "pending" && row.student_status === "accepted") return "待教师确认";
  if (row.teacher_status === "accepted" && row.student_status === "accepted") return "待确认";
  if (row.teacher_status === "accepted") return "老师已接受";
  if (row.student_status === "accepted") return "学生已接受";
  return "待处理";
}


function statusClass(row: any) {
  if (row.final_status === "confirmed") return "badge-green";
  if (row.final_status === "rejected") return "badge-amber";
  return "badge-blue";
}


async function load() {
  const resp = await axios.get("/api/admin/projects", {
    params: { page: page.value, page_size: pageSize.value }
  });
  projects.value = resp.data.items || [];
  total.value = resp.data.total || 0;
  if (projects.value.length && !selectedId.value) {
    selectedId.value = projects.value[0].id;
  }
}


function select(id: number) {
  selectedId.value = id;
}


function handlePageChange(p: number) {
  page.value = p;
  selectedId.value = null;
  load();
}


function openEdit(p: any) {
  editForm.value = {
    id: p.id,
    title: p.title,
    content: p.content,
    post_type: p.post_type,
    recruit_count: p.recruit_count,
    duration: p.duration || "",
    outcome: p.outcome || "",
    contact: p.contact || ""
  };
  editVisible.value = true;
}


async function saveEdit() {
  if (!editForm.value.title || !editForm.value.content) return;
  await axios.put(`/api/admin/projects/${editForm.value.id}`, {
    title: editForm.value.title,
    content: editForm.value.content,
    post_type: editForm.value.post_type,
    recruit_count: editForm.value.recruit_count,
    duration: editForm.value.duration || null,
    outcome: editForm.value.outcome || null,
    contact: editForm.value.contact || null
  });
  editVisible.value = false;
  await load();
}


async function remove(p: any) {
  if (!window.confirm("确认删除该项目？")) return;
  await axios.delete(`/api/admin/projects/${p.id}`);
  selectedId.value = null;
  await load();
}


onMounted(() => {
  load();
});
</script>
