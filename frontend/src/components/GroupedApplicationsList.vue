<template>
  <div class="grouped-applications">
    <!-- 筛选区域 -->
    <div class="filter-bar" v-if="!loading && groups.length > 0">
      <el-select
        v-model="roleFilter"
        placeholder="按角色筛选"
        clearable
        size="small"
        style="width: 160px;"
        @change="fetchGroupedApplications"
      >
        <el-option
          v-for="role in availableRoles"
          :key="role"
          :label="role"
          :value="role"
        />
      </el-select>
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="error-container">
      <el-alert type="error" :title="error" :closable="false" />
    </div>

    <div v-else-if="groups.length === 0" class="empty-container">
      <el-empty description="暂无申请" />
    </div>

    <div v-else class="groups-container">
      <el-scrollbar class="groups-scroll">
        <el-collapse v-model="activeNames" accordion>
          <el-collapse-item
            v-for="group in groups"
            :key="group.project.id"
            :name="group.project.id"
          >
          <template #title>
            <div class="group-header">
              <span class="project-title">{{ group.project.title }}</span>
              <el-badge
                v-if="group.pending_count > 0"
                :value="group.pending_count"
                type="warning"
                class="pending-badge"
              >
                <span class="badge-text">待处理</span>
              </el-badge>
              <span class="total-count">
                共 {{ group.applications.length }} 个申请
              </span>
            </div>
          </template>

          <div class="applications-list">
            <div
              v-for="app in group.applications"
              :key="app.id"
              class="application-item"
              @click="handleViewApplication(app)"
            >
              <div class="app-info">
                <div class="student-name">
                  <el-icon style="margin-right: 4px;"><User /></el-icon>
                  {{ app.student?.display_name || '未知学生' }}
                </div>
                <div class="app-meta">
                  <span class="app-time">
                    <el-icon style="margin-right: 2px;"><Clock /></el-icon>
                    {{ formatDate(app.created_at) }}
                  </span>
                  <el-tag
                    :type="getStatusType(app.final_status)"
                    size="small"
                  >
                    {{ getStatusText(app.final_status) }}
                  </el-tag>
                </div>
                <!-- 申请角色标签 -->
                <div v-if="app.applied_roles?.length" class="app-roles">
                  <span class="roles-label">申请角色：</span>
                  <el-tag
                    v-for="role in app.applied_roles"
                    :key="role"
                    size="small"
                    type="primary"
                    style="margin-right: 4px;"
                  >
                    {{ role }}
                  </el-tag>
                </div>
                <!-- 建议角色标签（教师邀请时） -->
                <div v-if="app.suggested_roles?.length" class="app-roles">
                  <span class="roles-label">建议角色：</span>
                  <el-tag
                    v-for="role in app.suggested_roles"
                    :key="role"
                    size="small"
                    type="success"
                    style="margin-right: 4px;"
                  >
                    {{ role }}
                  </el-tag>
                </div>
                <div v-if="app.applied_roles?.length || app.custom_status" class="app-extra">
                  <template v-if="app.applied_roles?.length">
                    <el-tag v-for="role in app.applied_roles" :key="role" size="small" type="info" style="margin-right: 4px;">
                      {{ role }}
                    </el-tag>
                  </template>
                  <el-tag v-if="app.custom_status" size="small" type="success">
                    状态：{{ app.custom_status }}
                  </el-tag>
                </div>
              </div>
              <el-icon class="arrow-icon"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
      </el-scrollbar>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, ArrowRight, User, Clock } from '@element-plus/icons-vue'
import axios from 'axios'

interface Application {
  id: number
  student: {
    id: number
    display_name: string
  } | null
  created_at: string
  final_status: string
  teacher_status: string
  student_status: string
  applied_roles?: string[]
  custom_status?: string
  suggested_roles?: string[]
}

interface GroupedApplication {
  project: {
    id: number
    title: string
    project_status: string
    required_roles?: string[]
  }
  applications: Application[]
  pending_count: number
}

interface Emits {
  (e: 'view-application', applicationId: number): void
}

const emit = defineEmits<Emits>()

const router = useRouter()
const loading = ref(false)
const error = ref('')
const groups = ref<GroupedApplication[]>([])
const activeNames = ref<number[]>([])
const roleFilter = ref('')
const availableRoles = ref<string[]>([])

onMounted(() => {
  loadAvailableRoles()
  fetchGroupedApplications()
})

// 加载可用的角色标签列表
const loadAvailableRoles = async () => {
  try {
    const response = await axios.get('/api/role-tags')
    availableRoles.value = response.data.all_tags || []
  } catch (err) {
    console.error('加载角色标签失败:', err)
  }
}

const fetchGroupedApplications = async () => {
  loading.value = true
  error.value = ''

  try {
    const params: any = {}
    if (roleFilter.value) {
      params.role = roleFilter.value
    }
    const response = await axios.get('/api/cooperation/requests/grouped-by-project', { params })
    groups.value = response.data.groups || []
    
    // 默认展开第一个有待处理申请的项目
    if (groups.value.length > 0) {
      const firstPending = groups.value.find(g => g.pending_count > 0)
      if (firstPending) {
        activeNames.value = [firstPending.project.id]
      }
    }
  } catch (err: any) {
    console.error('获取申请列表失败:', err)
    error.value = err.response?.data?.message || '加载失败，请重试'
  } finally {
    loading.value = false
  }
}

const handleViewApplication = (app: Application) => {
  // 跳转到项目管理页面，并选中对应的项目
  if (app.id) {
    // 通过路由参数传递项目ID和申请ID
    const projectId = groups.value.find(g => 
      g.applications.some(a => a.id === app.id)
    )?.project.id;
    
    if (projectId) {
      // 使用 Vue Router 跳转到教师项目管理页面
      router.push({
        name: 'teacher-posts',
        query: { project_id: String(projectId), request_id: String(app.id) }
      });
    }
  }
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    'pending': 'warning',
    'confirmed': 'success',
    'rejected': 'info'
  }
  return typeMap[status] || ''
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'pending': '待处理',
    'confirmed': '已确认',
    'rejected': '已拒绝'
  }
  return textMap[status] || status
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return minutes <= 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 暴露刷新方法供父组件调用
defineExpose({
  refresh: fetchGroupedApplications
})
</script>

<style scoped>
.grouped-applications {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.filter-bar {
  padding: 8px 0 12px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 8px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
}

.error-container {
  padding: 20px;
}

.empty-container {
  padding: 40px 20px;
}

.groups-container {
  width: 100%;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.groups-scroll {
  flex: 1 1 auto;
  min-height: 0;
}

.groups-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.groups-scroll :deep(.el-scrollbar__view) {
  padding-bottom: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding-right: 20px;
}

.project-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.pending-badge {
  margin-right: 8px;
}

.badge-text {
  font-size: 14px;
  color: #909399;
}

.total-count {
  font-size: 14px;
  color: #909399;
}

.applications-list {
  padding: 8px 0;
}

.application-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  margin-bottom: 8px;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.application-item:hover {
  background: #f0f2f5;
  transform: translateX(4px);
}

.application-item:last-child {
  margin-bottom: 0;
}

.app-info {
  flex: 1;
}

.student-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.app-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.app-time {
  font-size: 14px;
  color: #909399;
}

.app-extra {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.app-roles {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.roles-label {
  font-size: 12px;
  color: #909399;
  margin-right: 4px;
}

.role-tag,
.status-tag {
  font-size: 13px;
  color: #606266;
  padding: 2px 8px;
  background: #e5e7eb;
  border-radius: 4px;
}

.arrow-icon {
  font-size: 18px;
  color: #c0c4cc;
  transition: transform 0.3s;
}

.application-item:hover .arrow-icon {
  transform: translateX(4px);
  color: #909399;
}
</style>
