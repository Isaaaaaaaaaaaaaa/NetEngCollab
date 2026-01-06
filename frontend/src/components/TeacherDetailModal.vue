<template>
  <el-dialog
    v-model="dialogVisible"
    title="教师详情"
    width="600px"
    @close="handleClose"
  >
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span style="margin-top: 8px; color: #909399;">加载教师信息中...</span>
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-result icon="error" :title="error">
        <template #extra>
          <el-button type="primary" @click="fetchTeacherDetail">重试</el-button>
        </template>
      </el-result>
    </div>
    
    <div v-else-if="teacherData" class="teacher-detail">
      <!-- 基本信息 -->
      <div class="info-section">
        <h3>{{ teacherData.display_name }}</h3>
        <div class="info-item" v-if="teacherData.title">
          <span class="label">职称：</span>
          <span>{{ teacherData.title }}</span>
        </div>
        <div class="info-item" v-if="teacherData.organization">
          <span class="label">单位：</span>
          <span>{{ teacherData.organization }}</span>
        </div>
        <div class="info-item" v-if="teacherData.email">
          <span class="label">邮箱：</span>
          <span>{{ teacherData.email }}</span>
        </div>
        <div class="info-item" v-if="teacherData.phone">
          <span class="label">电话：</span>
          <span>{{ teacherData.phone }}</span>
        </div>
      </div>

      <!-- 简介 -->
      <div class="info-section" v-if="teacherData.bio">
        <h4>个人简介</h4>
        <p class="bio-text">{{ teacherData.bio }}</p>
      </div>

      <!-- 研究方向 -->
      <div class="info-section" v-if="teacherData.research_tags && teacherData.research_tags.length > 0">
        <h4>研究方向</h4>
        <div class="tags">
          <el-tag v-for="tag in teacherData.research_tags" :key="tag" type="info">
            {{ tag }}
          </el-tag>
        </div>
      </div>

      <!-- 统计数据 -->
      <div class="info-section" v-if="teacherData.stats">
        <h4>统计信息</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ teacherData.stats.total_projects || 0 }}</div>
            <div class="stat-label">发布项目</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ teacherData.stats.confirmed_projects || 0 }}</div>
            <div class="stat-label">确认合作</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">
              {{ teacherData.stats.success_rate ? (teacherData.stats.success_rate * 100).toFixed(0) + '%' : 'N/A' }}
            </div>
            <div class="stat-label">成功率</div>
          </div>
        </div>
      </div>

      <!-- 最近成就 -->
      <div class="info-section" v-if="teacherData.recent_achievements && teacherData.recent_achievements.length > 0">
        <h4>最近成就</h4>
        <ul class="achievements-list">
          <li v-for="(achievement, index) in teacherData.recent_achievements" :key="index">
            {{ achievement }}
          </li>
        </ul>
      </div>

      <!-- 自动回复设置 -->
      <div class="info-section" v-if="teacherData.auto_reply">
        <h4>回复时间</h4>
        <p class="auto-reply-text">{{ teacherData.auto_reply }}</p>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="handleSendMessage">发私信</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import axios from 'axios'

interface Props {
  visible: boolean
  teacherId: number | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'send-message', teacherId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const error = ref('')
const teacherData = ref<any>(null)

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal && props.teacherId) {
    fetchTeacherDetail()
  }
})

watch(dialogVisible, (newVal) => {
  if (!newVal) {
    emit('update:visible', false)
  }
})

const fetchTeacherDetail = async () => {
  if (!props.teacherId) return
  
  loading.value = true
  error.value = ''
  teacherData.value = null
  
  try {
    const response = await axios.get(`/api/teachers/${props.teacherId}/profile`)
    teacherData.value = response.data
  } catch (err: any) {
    console.error('获取教师信息失败:', err)
    if (err.response?.status === 404) {
      error.value = '教师信息不存在'
    } else {
      error.value = '加载失败，请重试'
    }
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
}

const handleSendMessage = () => {
  if (props.teacherId) {
    emit('send-message', props.teacherId)
    handleClose()
  }
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

.teacher-detail {
  max-height: 600px;
  overflow-y: auto;
}

.info-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.info-section:last-child {
  border-bottom: none;
}

.info-section h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #303133;
}

.info-section h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #606266;
}

.info-item {
  margin-bottom: 8px;
  line-height: 1.6;
}

.info-item .label {
  font-weight: 500;
  color: #909399;
  margin-right: 8px;
}

.bio-text {
  line-height: 1.8;
  color: #606266;
  margin: 0;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.achievements-list {
  margin: 0;
  padding-left: 20px;
}

.achievements-list li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

.auto-reply-text {
  line-height: 1.6;
  color: #606266;
  margin: 0;
  padding: 12px;
  background: #f0f9ff;
  border-left: 3px solid #409eff;
  border-radius: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
