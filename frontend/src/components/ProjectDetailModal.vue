<template>
  <el-dialog
    v-model="dialogVisible"
    title="项目详情"
    width="700px"
    @close="handleClose"
  >
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span style="margin-top: 8px; color: #909399;">加载项目详情中...</span>
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-result icon="error" :title="error">
        <template #extra>
          <el-button type="primary" @click="fetchProjectDetail">重试</el-button>
        </template>
      </el-result>
    </div>
    
    <div v-else-if="projectData" class="project-detail">
      <!-- 项目标题和状态 -->
      <div class="header-section">
        <h3>{{ projectData.title }}</h3>
        <el-tag :type="getStatusType(projectData.project_status)">
          {{ getStatusText(projectData.project_status) }}
        </el-tag>
      </div>

      <!-- 项目基本信息 -->
      <div class="info-section">
        <div class="info-row">
          <span class="label">项目类型：</span>
          <span>{{ getProjectTypeText(projectData.post_type) }}</span>
        </div>
        <div class="info-row" v-if="projectData.project_level">
          <span class="label">项目级别：</span>
          <span>{{ projectData.project_level }}</span>
        </div>
        <div class="info-row" v-if="projectData.recruit_count">
          <span class="label">招募人数：</span>
          <span>{{ projectData.recruit_count }} 人</span>
        </div>
        <div class="info-row" v-if="projectData.duration">
          <span class="label">项目周期：</span>
          <span>{{ projectData.duration }}</span>
        </div>
        <div class="info-row" v-if="projectData.deadline">
          <span class="label">截止日期：</span>
          <span>{{ formatDate(projectData.deadline) }}</span>
        </div>
      </div>

      <!-- 项目简介 -->
      <div class="info-section">
        <h4>项目简介</h4>
        <p class="content-text">{{ projectData.content }}</p>
      </div>

      <!-- 项目详细信息（富文本） -->
      <div class="info-section" v-if="projectData.detailed_info">
        <h4>详细信息</h4>
        <div class="detailed-info" v-html="projectData.detailed_info"></div>
      </div>

      <!-- 技术栈 -->
      <div class="info-section" v-if="projectData.tech_stack && projectData.tech_stack.length > 0">
        <h4>技术栈</h4>
        <div class="tags">
          <el-tag v-for="tech in projectData.tech_stack" :key="tech" type="success">
            {{ tech }}
          </el-tag>
        </div>
      </div>

      <!-- 项目标签 -->
      <div class="info-section" v-if="projectData.tags && projectData.tags.length > 0">
        <h4>项目标签</h4>
        <div class="tags">
          <el-tag v-for="tag in projectData.tags" :key="tag">
            {{ tag }}
          </el-tag>
        </div>
      </div>

      <!-- 预期成果 -->
      <div class="info-section" v-if="projectData.outcome">
        <h4>预期成果</h4>
        <p class="content-text">{{ projectData.outcome }}</p>
      </div>

      <!-- 联系方式 -->
      <div class="info-section" v-if="projectData.contact">
        <h4>联系方式</h4>
        <p class="content-text">{{ projectData.contact }}</p>
      </div>

      <!-- 立项书/往期成果附件 -->
      <div class="info-section" v-if="projectData.attachment_file_id">
        <h4>立项书 / 往期成果附件</h4>
        <div class="attachment-link">
          <el-button type="primary" link @click="downloadAttachment">
            <el-icon style="margin-right: 4px;"><Download /></el-icon>
            下载附件
          </el-button>
        </div>
      </div>

      <!-- 教师信息 -->
      <div class="info-section" v-if="projectData.teacher">
        <h4>指导教师</h4>
        <div class="teacher-info">
          <span class="teacher-name">{{ projectData.teacher.display_name }}</span>
          <span v-if="projectData.teacher.title" class="teacher-title">
            （{{ projectData.teacher.title }}）
          </span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <template v-if="showApplyButton && projectData">
          <template v-if="requestStatus">
            <el-tag :type="requestStatus.final_status === 'confirmed' ? 'success' : requestStatus.final_status === 'rejected' ? 'warning' : 'info'">
              {{ getApplyStatusText() }}
            </el-tag>
          </template>
          <template v-else-if="canApply()">
            <el-button type="primary" @click="handleApply">申请加入</el-button>
          </template>
          <template v-else>
            <el-tag type="info">{{ getUnavailableReason() }}</el-tag>
          </template>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Loading, Download } from '@element-plus/icons-vue'
import axios from 'axios'

interface Props {
  visible: boolean
  projectId: number | null
  showApplyButton?: boolean
  requestStatus?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'apply', projectId: number): void
}

const props = withDefaults(defineProps<Props>(), {
  showApplyButton: false,
  requestStatus: null
})
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const error = ref('')
const projectData = ref<any>(null)

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal && props.projectId) {
    fetchProjectDetail()
  }
})

watch(dialogVisible, (newVal) => {
  if (!newVal) {
    emit('update:visible', false)
  }
})

const fetchProjectDetail = async () => {
  if (!props.projectId) return
  
  loading.value = true
  error.value = ''
  projectData.value = null
  
  try {
    const response = await axios.get('/api/teacher-posts', {
      params: { page: 1, page_size: 1000 }
    })
    
    const project = response.data.items.find((item: any) => item.id === props.projectId)
    
    if (project) {
      projectData.value = project
    } else {
      error.value = '项目不存在或已删除'
    }
  } catch (err: any) {
    console.error('获取项目详情失败:', err)
    error.value = '加载失败，请重试'
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
}

const downloadAttachment = () => {
  if (projectData.value?.attachment_file_id) {
    window.open(`/api/files/${projectData.value.attachment_file_id}`, '_blank')
  }
}

// 检查是否可以申请
const canApply = () => {
  if (!projectData.value) return false
  
  // 已经申请过的不能再申请
  if (props.requestStatus) return false
  
  // 检查是否已满员
  if (projectData.value.confirmed_count !== undefined && projectData.value.recruit_count) {
    if (projectData.value.confirmed_count >= projectData.value.recruit_count) return false
  }
  
  // 检查项目状态
  if (projectData.value.project_status && projectData.value.project_status !== 'recruiting') return false
  
  // 检查截止时间
  if (projectData.value.deadline) {
    const deadline = new Date(projectData.value.deadline)
    if (deadline < new Date()) return false
  }
  
  return true
}

// 获取申请状态文本
const getApplyStatusText = () => {
  if (!props.requestStatus) return ''
  
  const r = props.requestStatus
  if (r.final_status === 'confirmed') return '已确认'
  if (r.final_status === 'rejected') return '已拒绝'
  if (r.teacher_status === 'accepted' && r.student_status === 'pending') return '待我确认'
  if (r.teacher_status === 'pending' && r.student_status === 'accepted') return '待教师确认'
  return '待审核'
}

// 获取不可申请的原因
const getUnavailableReason = () => {
  if (!projectData.value) return ''
  
  // 检查是否已满员
  if (projectData.value.confirmed_count !== undefined && projectData.value.recruit_count) {
    if (projectData.value.confirmed_count >= projectData.value.recruit_count) return '已满员'
  }
  
  // 检查项目状态
  if (projectData.value.project_status === 'in_progress') return '进行中'
  if (projectData.value.project_status === 'completed') return '已完成'
  if (projectData.value.project_status === 'closed') return '已关闭'
  
  // 检查截止时间
  if (projectData.value.deadline) {
    const deadline = new Date(projectData.value.deadline)
    if (deadline < new Date()) return '已截止'
  }
  
  return '不可申请'
}

// 申请加入
const handleApply = () => {
  if (props.projectId) {
    emit('apply', props.projectId)
  }
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    'recruiting': 'success',
    'in_progress': 'warning',
    'completed': 'info'
  }
  return typeMap[status] || ''
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'recruiting': '招募中',
    'in_progress': '进行中',
    'completed': '已完成'
  }
  return textMap[status] || status
}

const getProjectTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    'project': '科研项目',
    'innovation': '大创项目',
    'competition': '学科竞赛'
  }
  return typeMap[type] || type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
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

.project-detail {
  max-height: 600px;
  overflow-y: auto;
}

.header-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #eee;
}

.header-section h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #303133;
  flex: 1;
}

.info-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.info-section:last-child {
  border-bottom: none;
}

.info-section h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #606266;
}

.info-row {
  margin-bottom: 8px;
  line-height: 1.8;
}

.info-row .label {
  font-weight: 500;
  color: #909399;
  margin-right: 8px;
}

.content-text {
  line-height: 1.8;
  color: #606266;
  margin: 0;
  white-space: pre-wrap;
}

.detailed-info {
  line-height: 1.8;
  color: #606266;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.detailed-info :deep(p) {
  margin: 0 0 12px 0;
}

.detailed-info :deep(p:last-child) {
  margin-bottom: 0;
}

.detailed-info :deep(ul),
.detailed-info :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.detailed-info :deep(strong) {
  font-weight: 600;
  color: #303133;
}

.detailed-info :deep(em) {
  font-style: italic;
}

.detailed-info :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.detailed-info :deep(a:hover) {
  text-decoration: underline;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.teacher-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.teacher-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.teacher-title {
  color: #909399;
  font-size: 14px;
}

.attachment-link {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  display: inline-block;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}
</style>
