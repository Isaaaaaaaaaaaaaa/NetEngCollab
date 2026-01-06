<template>
  <div class="page cp-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">合作项目进展</h2>
        <p class="page-subtitle">查看你已确认加入的项目里程碑与进度更新</p>
      </div>
    </div>

    <el-row :gutter="16" class="cp-main" style="margin-top: 6px;">
      <el-col :xs="24" :lg="6">
        <el-card class="app-card cp-card" shadow="never">
          <template #header>
            <div class="page-subtitle">我的合作项目</div>
          </template>
          <el-empty v-if="!projects.length" description="暂无合作项目" />
          <el-scrollbar v-else class="cp-scroll">
            <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text);">
              <li
                v-for="p in projects"
                :key="p.id"
                style="padding:6px 8px; border-radius:8px; cursor:pointer;"
                :style="p.id === selectedId ? 'background:#eff4ff;' : 'background:transparent;'"
                @click="select(p.id)"
              >
                <div class="truncate" style="max-width:200px; font-weight: 500;">{{ p.title }}</div>
                <div v-if="(p.my_applied_roles && p.my_applied_roles.length) || p.my_custom_status" style="margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px;">
                  <template v-if="p.my_applied_roles && p.my_applied_roles.length">
                    <span v-for="role in p.my_applied_roles" :key="role" class="tag" style="font-size: 10px;">{{ role }}</span>
                  </template>
                  <span v-if="p.my_custom_status" class="pill badge-blue" style="font-size: 10px;">{{ p.my_custom_status }}</span>
                </div>
              </li>
            </ul>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="app-card cp-card" shadow="never">
          <template #header>
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <div class="page-subtitle">里程碑</div>
              <el-button 
                v-if="selectedProject" 
                size="small" 
                type="primary" 
                text
                @click="openStatusDialog"
              >
                设置我的状态
              </el-button>
            </div>
          </template>
          <el-empty v-if="!selectedId" description="请选择左侧项目" />
          <div v-else class="cp-section">
            <!-- 我的状态信息 -->
            <div v-if="selectedProject" style="margin-bottom: 12px; padding: 8px; background: #f5f7fa; border-radius: 6px;">
              <div style="font-size: 12px; color: var(--app-muted); margin-bottom: 4px;">我在项目中的信息</div>
              <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px;">
                <span>
                  角色：
                  <template v-if="selectedProject.my_applied_roles && selectedProject.my_applied_roles.length">
                    <span v-for="(role, idx) in selectedProject.my_applied_roles" :key="role" style="font-weight: 500;">
                      {{ role }}<template v-if="idx < selectedProject.my_applied_roles.length - 1">、</template>
                    </span>
                  </template>
                  <span v-else style="font-weight: 500;">未设置</span>
                </span>
                <span>
                  状态：
                  <span class="pill badge-blue" style="font-size: 11px;">{{ selectedProject.my_custom_status || '未设置' }}</span>
                </span>
              </div>
            </div>
            
            <el-empty v-if="!milestones.length" description="暂无里程碑" />
            <el-scrollbar v-else class="cp-scroll" style="padding-right: 6px;">
              <el-timeline>
                <el-timeline-item
                  v-for="m in milestones"
                  :key="m.id"
                  size="small"
                  :type="m.status === 'done' ? 'success' : m.is_near_due ? 'danger' : 'warning'"
                >
                  <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                    <div style="display:flex; flex-direction:column; gap:2px; max-width:240px;">
                      <span class="truncate">{{ m.title }}</span>
                      <span v-if="m.due_date" style="font-size:10px; color:var(--app-muted);">
                        截止 {{ m.due_date.slice(0, 10) }}
                      </span>
                    </div>
                    <span v-if="m.status === 'done'" class="pill badge-green">已完成</span>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </el-scrollbar>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="app-card cp-card" shadow="never">
          <template #header>
            <div class="page-subtitle">进度更新</div>
          </template>
          <el-empty v-if="!selectedId" description="请选择左侧项目" />
          <div v-else class="cp-section">
            <el-empty v-if="!updates.length" description="暂无更新" />
            <el-scrollbar v-else class="cp-scroll">
              <ul style="list-style:none; padding:0; margin:0; font-size:12px; color:var(--app-text); padding-right:6px;">
                <li
                  v-for="u in updates"
                  :key="u.id"
                  style="padding:6px 0; border-bottom:1px solid rgba(148,163,184,0.25);"
                >
                  <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                    <span v-if="u.author_name" style="font-weight: 500; color: var(--app-primary);">{{ u.author_name }}</span>
                  </div>
                  <div style="margin-bottom:2px; white-space: pre-wrap; word-break: break-word;">{{ u.content }}</div>
                  <div style="font-size:10px; color:var(--app-muted);">
                    {{ u.created_at?.slice(0, 16).replace('T', ' ') }}
                  </div>
                </li>
              </ul>
            </el-scrollbar>

            <div class="cp-form">
              <el-input
                v-model="updateContent"
                type="textarea"
                :rows="3"
                placeholder="记录你的进展、遇到的问题与下一步计划"
              />
              <el-button
                type="primary"
                size="small"
                style="width:100%; margin-top:6px;"
                @click="addUpdate"
              >
                提交更新
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设置状态弹窗 -->
    <el-dialog v-model="statusDialogVisible" title="设置我的状态" width="450px">
      <el-form :model="statusForm" label-position="top" size="small">
        <el-form-item label="我的角色">
          <RoleTagSelector
            v-model="statusForm.applied_roles"
            :suggested-tags="selectedProject?.required_roles || []"
            hint="选择您在项目中的角色"
          />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-select v-model="statusForm.custom_status" placeholder="选择或输入状态" filterable allow-create clearable style="width: 100%;">
            <el-option label="进展顺利" value="进展顺利" />
            <el-option label="需要帮助" value="需要帮助" />
            <el-option label="已完成阶段任务" value="已完成阶段任务" />
            <el-option label="待分配任务" value="待分配任务" />
            <el-option label="学习中" value="学习中" />
            <el-option label="暂时搁置" value="暂时搁置" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="text-align: right;">
          <el-button size="small" @click="statusDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" @click="saveStatus">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import RoleTagSelector from "../../components/RoleTagSelector.vue";


const projects = ref<any[]>([]);
const selectedId = ref<number | null>(null);
const milestones = ref<any[]>([]);
const updates = ref<any[]>([]);
const updateContent = ref("");
const statusDialogVisible = ref(false);
const statusForm = reactive({
  applied_roles: [] as string[],
  custom_status: ""
});

// 计算当前选中的项目
const selectedProject = computed(() => {
  if (!selectedId.value) return null;
  return projects.value.find(p => p.id === selectedId.value) || null;
});


async function loadProjects() {
  const resp = await axios.get("/api/cooperation/projects");
  projects.value = resp.data.items;
  if (projects.value.length && !selectedId.value) {
    selectedId.value = projects.value[0].id;
    await loadDetails();
  }
}


async function loadDetails() {
  if (!selectedId.value) return;
  const [msResp, upResp] = await Promise.all([
    axios.get(`/api/posts/${selectedId.value}/milestones`),
    axios.get(`/api/posts/${selectedId.value}/updates`)
  ]);
  milestones.value = msResp.data.items;
  updates.value = upResp.data.items;
}


function select(id: number) {
  selectedId.value = id;
  loadDetails();
}


async function addUpdate() {
  if (!selectedId.value || !updateContent.value) return;
  await axios.post(`/api/posts/${selectedId.value}/updates`, { content: updateContent.value });
  updateContent.value = "";
  await loadDetails();
}


function openStatusDialog() {
  if (!selectedProject.value) return;
  statusForm.applied_roles = selectedProject.value.my_applied_roles || [];
  statusForm.custom_status = selectedProject.value.my_custom_status || "";
  statusDialogVisible.value = true;
}


async function saveStatus() {
  if (!selectedProject.value || !selectedProject.value.my_request_id) {
    ElMessage.error("无法获取合作请求信息");
    return;
  }
  
  try {
    await axios.put(`/api/cooperation/requests/${selectedProject.value.my_request_id}/student-info`, {
      applied_roles: statusForm.applied_roles,
      custom_status: statusForm.custom_status || null
    });
    
    ElMessage.success("状态更新成功");
    statusDialogVisible.value = false;
    
    // 重新加载项目列表以更新状态
    await loadProjects();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || "更新失败");
  }
}


onMounted(() => {
  loadProjects();
});
</script>

<style scoped>
.cp-page {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cp-main {
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
  overflow: hidden;
}

.cp-main :deep(.el-col) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.cp-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cp-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cp-section {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.cp-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.cp-form {
  flex: 0 0 auto;
  margin-top: 8px;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
