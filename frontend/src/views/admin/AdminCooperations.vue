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
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";


const projects = ref<any[]>([]);
const selectedId = ref<number | null>(null);


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
  const resp = await axios.get("/api/admin/projects");
  projects.value = resp.data.items || [];
  if (projects.value.length && !selectedId.value) {
    selectedId.value = projects.value[0].id;
  }
}


function select(id: number) {
  selectedId.value = id;
}


onMounted(() => {
  load();
});
</script>
