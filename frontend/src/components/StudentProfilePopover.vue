<template>
  <el-popover
    :visible="visible"
    placement="right"
    :width="320"
    trigger="click"
    :show-after="0"
    :hide-after="0"
    @show="handleShow"
    @hide="handleHide"
  >
    <template #reference>
      <span @click.stop="toggleVisible" style="cursor: pointer;">
        <slot></slot>
      </span>
    </template>
    
    <div class="profile-popover">
      <!-- 关闭按钮 -->
      <div class="popover-close" @click="closePopover">
        <el-icon><Close /></el-icon>
      </div>
      
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="error" class="error-state">
        <span>{{ error }}</span>
      </div>
      
      <div v-else-if="profile" class="profile-content">
        <!-- 头部信息 -->
        <div class="profile-header">
          <div class="profile-name">{{ profile.display_name }}</div>
          <div class="profile-meta">
            <span v-if="profile.grade">{{ profile.grade }}</span>
            <span v-if="profile.major">{{ profile.major }}</span>
          </div>
        </div>
        
        <!-- 评分和时间 -->
        <div class="profile-stats">
          <div class="stat-item">
            <span class="stat-label">技能评分</span>
            <span class="stat-value">{{ profile.skill_score || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">每周可用</span>
            <span class="stat-value">{{ profile.weekly_hours || 0 }}h</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">项目经历</span>
            <span class="stat-value">{{ profile.experiences_count || 0 }}个</span>
          </div>
        </div>
        
        <!-- 技能标签 -->
        <div v-if="profile.skills && profile.skills.length" class="profile-section">
          <div class="section-title">技能</div>
          <div class="skill-tags">
            <span 
              v-for="skill in profile.skills.slice(0, 6)" 
              :key="skill.name" 
              class="skill-tag"
              :class="skillLevelClass(skill.level)"
            >
              {{ skill.name }}
              <span v-if="skill.level" class="skill-level">{{ skill.level }}</span>
            </span>
            <span v-if="profile.skills.length > 6" class="more-tag">+{{ profile.skills.length - 6 }}</span>
          </div>
        </div>
        
        <!-- 兴趣方向 -->
        <div v-if="profile.interests && profile.interests.length" class="profile-section">
          <div class="section-title">兴趣方向</div>
          <div class="interest-tags">
            <span v-for="interest in profile.interests.slice(0, 4)" :key="interest" class="interest-tag">
              {{ interest }}
            </span>
            <span v-if="profile.interests.length > 4" class="more-tag">+{{ profile.interests.length - 4 }}</span>
          </div>
        </div>
        
        <!-- 最近经历 -->
        <div v-if="profile.recent_experiences && profile.recent_experiences.length" class="profile-section">
          <div class="section-title">最近经历</div>
          <div class="experience-list">
            <div v-for="exp in profile.recent_experiences.slice(0, 2)" :key="exp.title" class="experience-item">
              <span class="exp-title truncate">{{ exp.title }}</span>
              <span class="exp-type">{{ exp.type }}</span>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="profile-actions">
          <el-button 
            v-if="profile.resume_file_id" 
            size="small" 
            type="primary" 
            link
            @click="downloadResume"
          >
            <el-icon style="margin-right: 4px;"><Download /></el-icon>
            下载简历
          </el-button>
          <el-button 
            size="small" 
            type="primary" 
            link
            @click="viewFullProfile"
          >
            查看完整画像
          </el-button>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Loading, Download, Close } from '@element-plus/icons-vue'

interface Props {
  studentId: number
}

const props = defineProps<Props>()
const router = useRouter()

const visible = ref(false)
const loading = ref(false)
const error = ref('')
const profile = ref<any>(null)

// 缓存已加载的学生画像
const profileCache = new Map<number, any>()

const toggleVisible = () => {
  visible.value = !visible.value
  if (visible.value) {
    loadProfile()
  }
}

const handleShow = () => {
  loadProfile()
}

const handleHide = () => {
  visible.value = false
}

// 点击外部关闭
const closePopover = () => {
  visible.value = false
}

const loadProfile = async () => {
  if (!props.studentId) return
  
  // 检查缓存
  if (profileCache.has(props.studentId)) {
    profile.value = profileCache.get(props.studentId)
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.get(`/api/students/${props.studentId}/summary`)
    profile.value = response.data
    profileCache.set(props.studentId, response.data)
  } catch (err: any) {
    console.error('加载学生画像失败:', err)
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
}

const skillLevelClass = (level: string) => {
  const levelMap: Record<string, string> = {
    '精通': 'level-expert',
    '熟练': 'level-proficient',
    '了解': 'level-basic'
  }
  return levelMap[level] || 'level-basic'
}

const downloadResume = () => {
  if (profile.value?.resume_file_id) {
    // 获取token用于认证
    const token = localStorage.getItem('token')
    const url = token 
      ? `/api/files/${profile.value.resume_file_id}?token=${encodeURIComponent(token)}`
      : `/api/files/${profile.value.resume_file_id}`
    window.open(url, '_blank')
  }
}

const viewFullProfile = () => {
  router.push({ name: 'teacher-students', query: { student_id: props.studentId } })
}

// 当studentId变化时清除当前profile
watch(() => props.studentId, () => {
  profile.value = null
})
</script>

<style scoped>
.profile-popover {
  min-height: 100px;
  position: relative;
}

.popover-close {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #909399;
  border-radius: 50%;
  transition: all 0.2s;
  z-index: 1;
}

.popover-close:hover {
  color: #409eff;
  background: #f0f9ff;
}

.loading-state,
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #909399;
  font-size: 13px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-header {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}

.profile-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.profile-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.profile-stats {
  display: flex;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}

.profile-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
}

.skill-tags,
.interest-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  background: #f0f9ff;
  color: #0369a1;
  border: 1px solid #bae6fd;
}

.skill-tag.level-expert {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.skill-tag.level-proficient {
  background: #d1fae5;
  color: #065f46;
  border-color: #6ee7b7;
}

.skill-level {
  font-size: 10px;
  opacity: 0.8;
}

.interest-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  background: #f3f4f6;
  color: #4b5563;
}

.more-tag {
  padding: 2px 6px;
  font-size: 10px;
  color: #909399;
}

.experience-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.experience-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
}

.exp-title {
  flex: 1;
  color: #606266;
}

.exp-type {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 3px;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 10px;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
